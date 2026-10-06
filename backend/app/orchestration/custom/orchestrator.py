import asyncio
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

from app.agents import (
    ActivityAgent, ActivityAgentInput,
    BudgetAgent, BudgetAgentInput,
    ConstraintAgent, ConstraintAgentInput,
    FlightAgent, FlightAgentInput,
    HotelAgent, HotelAgentInput,
    WeatherAgent, WeatherAgentInput,
)
from app.agents.base import AgentResult
from app.llm.base import LLMProvider
from app.schemas import Itinerary
from app.schemas.state import TravelRequest, TravelState, WorkflowEvent
from app.orchestration.custom.replanner import Replanner
from app.orchestration.agent_retry import run_agent_with_retry
from app.orchestration.rules import FOOD_PER_PERSON_PER_DAY, TRANSPORT_PER_PERSON_PER_DAY, hotel_cap

logger = logging.getLogger(__name__)




class TravelOrchestrator:
    """
    Drives one planning run: state -> parallel research -> select ->
    budget -> constraints -> completed / failed.
    """

    def __init__(
        self,
        *,
        flight_agent: Any,
        hotel_agent: Any,
        activity_agent: Any,
        weather_agent: Any,
        budget_agent: BudgetAgent,
        constraint_agent: ConstraintAgent,
        replanner: Replanner | None = None,
        retry_delay: float = 1.0,
    ):
        self.flight_agent = flight_agent
        self.hotel_agent = hotel_agent
        self.activity_agent = activity_agent
        self.weather_agent = weather_agent
        self.budget_agent = budget_agent
        self.constraint_agent = constraint_agent
        self.replanner = replanner or Replanner()
        self.retry_delay = retry_delay

    @classmethod
    def from_llm(cls, llm: LLMProvider, retry_delay: float = 1.0) -> "TravelOrchestrator":
        return cls(
            flight_agent=FlightAgent(llm),
            hotel_agent=HotelAgent(llm),
            activity_agent=ActivityAgent(llm),
            weather_agent=WeatherAgent(llm),
            budget_agent=BudgetAgent(llm),
            constraint_agent=ConstraintAgent(llm),
            replanner=Replanner(),
            retry_delay=retry_delay,
        )
    # ------------------------------------------------------------------
    # The workflow
    # ------------------------------------------------------------------

    async def run(self, request: TravelRequest) -> TravelState:
        state = TravelState(request=request)
        self._emit(state, "planning_started", f"Planning trip to {request.destination}")

        while True:
            await self._run_research(state)

            if not state.flights or not state.hotels:
                return self._fail(state, "Cannot build a plan without flights and hotels")

            self._select(state)
            await self._check_budget(state)
            await self._check_constraints(state)

            if state.constraint_result.passed:
                return self._complete(state)

            if not self.replanner.should_replan(state):
                return self._fail(state, f"Constraints failed after {state.iteration} replan(s)")

            self.replanner.replan(state)
            # Loop back to _run_research with the updated strategy/cap.

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _run_research(self, state: TravelState) -> None:
        req = state.request
        check_in = req.start_date
        check_out = req.start_date + timedelta(days=req.duration_days)

        # gather starts all four coroutines together and waits for all of them.
        # _run_agent never raises, so one failing agent cannot cancel the others.
        flight, hotel, activity, weather = await asyncio.gather(
            self._run_agent(state, "flight", self.flight_agent, FlightAgentInput(
                origin=req.origin,
                destination=req.destination,
                departure_date=check_in.isoformat(),
                travellers=req.travellers,
                currency=req.currency,
            )),
            self._run_agent(state, "hotel", self.hotel_agent, HotelAgentInput(
                city=req.destination,
                check_in=check_in.isoformat(),
                check_out=check_out.isoformat(),
                guests=req.travellers,
                max_price_per_night=float(self._hotel_cap(req)),
                currency=req.currency,
            )),
            self._run_agent(state, "activity", self.activity_agent, ActivityAgentInput(
                city=req.destination,
                interests=req.interests,
            )),
            self._run_agent(state, "weather", self.weather_agent, WeatherAgentInput(
                city=req.destination,
                target_date=check_in.isoformat(),
            )),
        )

        # Write results into the state only after every agent has finished.
        if flight:
            state.flights = flight.data.flights
        if hotel:
            state.hotels = hotel.data.selected_hotels
        if activity:
            state.activities = activity.data.activities
        if weather:
            state.weather = weather.data.weather

    async def _run_agent(self, state: TravelState, name: str, agent: Any, agent_input: Any):
        self._emit(state, f"{name}_started", f"{name} agent started")
        result, error = await run_agent_with_retry(
            run_id=state.run_id, name=name, agent=agent, agent_input=agent_input, delay=self.retry_delay,
        )
        if result is not None:
            self._emit(state, f"{name}_completed", f"{name} agent completed")
            return result
        state.errors.append(f"{name} agent failed: {error}")
        self._emit(state, f"{name}_failed", f"{name} agent failed: {error}")
        return None

    def _select(self, state: TravelState) -> None:
        """Python picks one flight and one hotel from the candidates."""
        pick = max if state.strategy == "comfort" else min
        state.selected_flight = pick(state.flights, key=lambda f: f.price)
        state.selected_hotel = pick(state.hotels, key=lambda h: h.price_per_night)
        self._emit(
            state, "selection_made",
            f"strategy={state.strategy} flight={state.selected_flight.id} hotel={state.selected_hotel.id}",
        )


    def _hotel_cap(self, req: TravelRequest) -> Decimal:
        return hotel_cap(req) 


    async def _check_budget(self, state: TravelState) -> None:
        req = state.request
        person_days = req.travellers * req.duration_days

        result = await self.budget_agent.run(BudgetAgentInput(
            budget=req.budget,
            flights=[state.selected_flight],
            hotels=[state.selected_hotel],
            activities=state.activities,
            transport=TRANSPORT_PER_PERSON_PER_DAY * person_days,
            food=FOOD_PER_PERSON_PER_DAY * person_days,
        ))
        state.budget_result = result.data.result

        event = "budget_calculated" if state.budget_result.passed else "budget_failed"
        self._emit(
            state, event,
            f"total={state.budget_result.total} budget={state.budget_result.budget} | {result.data.explanation}",
        )

    async def _check_constraints(self, state: TravelState) -> None:
        req = state.request

        result = await self.constraint_agent.run(ConstraintAgentInput(
            total_cost=state.budget_result.total,
            budget=req.budget,
            hotels=[state.selected_hotel],
            max_hotel_price_per_night=self._hotel_cap(req),
            # The plan carries no traveller count yet, so this pair is trivially equal.
            travellers=req.travellers,
            expected_travellers=req.travellers,
            duration_days=state.selected_hotel.nights,
            expected_duration_days=req.duration_days,
        ))
        state.constraint_result = result.data.result

        if state.constraint_result.passed:
            self._emit(state, "constraints_passed", "All constraints satisfied")
        else:
            names = ", ".join(v.constraint for v in state.constraint_result.violations)
            self._emit(state, "constraints_failed", f"Violations: {names}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    

    def _complete(self, state: TravelState) -> TravelState:
        req = state.request
        summary = (
            f"{req.travellers} travellers, {req.duration_days} days in {req.destination}. "
            f"Flight: {state.selected_flight.airline}. Hotel: {state.selected_hotel.name}. "
            f"{len(state.activities)} activities. "
            f"Total {state.budget_result.total} of {req.budget} {req.currency}."
        )
        if state.weather:
            summary += f" Expected weather: {state.weather.condition}, {state.weather.temperature_celsius}°C."

        state.itinerary = Itinerary(
            destination=req.destination,
            duration_days=req.duration_days,
            total_cost=state.budget_result.total,
            currency=req.currency,
            summary=summary,
        )
        state.status = "completed"
        self._emit(state, "planning_completed", "Planning completed")
        return state

    def _fail(self, state: TravelState, reason: str) -> TravelState:
        state.status = "failed"
        state.errors.append(reason)
        self._emit(state, "planning_failed", reason)
        return state

    def _emit(self, state: TravelState, event_type: str, message: str) -> None:
        state.events.append(WorkflowEvent(run_id=state.run_id, event_type=event_type, message=message))
        logger.info("run=%s event=%s %s", state.run_id, event_type, message)