import asyncio
import logging
from datetime import timedelta
from typing import Any

from app.embeddings.local_provider import SentenceTransformerProvider
from app.services.retriever_service import RetrieverService

from app.agents import (
    ActivityAgent, ActivityAgentInput,
    BudgetAgent, BudgetAgentInput,
    ConstraintAgent, ConstraintAgentInput,
    FlightAgent, FlightAgentInput,
    HotelAgent, HotelAgentInput,
    WeatherAgent, WeatherAgentInput,
)
from app.llm.base import LLMProvider
from app.orchestration.agent_retry import run_agent_with_retry
from app.orchestration.custom.replanner import Replanner
from app.orchestration.rules import FOOD_PER_PERSON_PER_DAY, TRANSPORT_PER_PERSON_PER_DAY, hotel_cap
from app.schemas import Itinerary
from app.schemas.state import TravelRequest, TravelState, WorkflowEvent
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class TravelOrchestrator:
    """
    Drives one planning run: state -> parallel research -> select ->
    budget -> constraints -> completed / failed, with replanning on
    constraint failure, and optional memory (preferences read in
    before planning, completed trips saved out after).
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
        memory_service: MemoryService | None = None,
        retry_delay: float = 1.0,
    ):
        self.flight_agent = flight_agent
        self.hotel_agent = hotel_agent
        self.activity_agent = activity_agent
        self.weather_agent = weather_agent
        self.budget_agent = budget_agent
        self.constraint_agent = constraint_agent
        self.replanner = replanner or Replanner()
        self.memory_service = memory_service
        self.retry_delay = retry_delay

    @classmethod
    def from_llm(
        cls, llm: LLMProvider, retry_delay: float = 1.0, memory_service: MemoryService | None = None,
    ) -> "TravelOrchestrator":
        return cls(
            flight_agent=FlightAgent(llm),
            hotel_agent=HotelAgent(llm),
            activity_agent=ActivityAgent(llm, retriever=RetrieverService(SentenceTransformerProvider())),
            weather_agent=WeatherAgent(llm),
            budget_agent=BudgetAgent(llm),
            constraint_agent=ConstraintAgent(llm),
            replanner=Replanner(),
            memory_service=memory_service,
            retry_delay=retry_delay,
        )

    # ------------------------------------------------------------------
    # The workflow
    # ------------------------------------------------------------------

    async def run(
        self, request: TravelRequest, user_id: int | None = None, event_sink=None,
    ) -> TravelState:
        state = TravelState(request=request)
        self._event_sink = event_sink
        self._emit(state, "planning_started", f"Planning trip to {request.destination}")

        preferences_text = await self._load_preferences(user_id)

        while True:
            await self._run_research(state, preferences_text)

            if not state.flights or not state.hotels:
                state = self._fail(state, "Cannot build a plan without flights and hotels")
                break

            self._select(state)
            await self._check_budget(state)
            await self._check_constraints(state)

            if state.constraint_result.passed:
                state = self._complete(state)
                break

            if not self.replanner.should_replan(state):
                state = self._fail(state, f"Constraints failed after {state.iteration} replan(s)")
                break

            self.replanner.replan(state)
            # loop back to research with the updated strategy/cap

        if state.status == "completed" and self.memory_service and user_id:
            await self.memory_service.save_trip(user_id, state)

        return state

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _load_preferences(self, user_id: int | None) -> str | None:
        if not self.memory_service or not user_id:
            return None
        prefs = await self.memory_service.get_preferences(user_id)
        if not prefs:
            return None
        return "; ".join(f"{p.key}: {p.value}" for p in prefs)

    async def _run_research(self, state: TravelState, preferences_text: str | None) -> None:
        req = state.request
        check_in = req.start_date
        check_out = req.start_date + timedelta(days=req.duration_days)

        flight, hotel, activity, weather = await asyncio.gather(
            self._run_agent(state, "flight", self.flight_agent, FlightAgentInput(
                origin=req.origin, destination=req.destination,
                departure_date=check_in.isoformat(), travellers=req.travellers, currency=req.currency,
            )),
            self._run_agent(state, "hotel", self.hotel_agent, HotelAgentInput(
                city=req.destination, check_in=check_in.isoformat(), check_out=check_out.isoformat(),
                guests=req.travellers, max_price_per_night=float(hotel_cap(req)), currency=req.currency,
                preferences=preferences_text,
            )),
            self._run_agent(state, "activity", self.activity_agent, ActivityAgentInput(
                city=req.destination, interests=req.interests, preferences=preferences_text,
            )),
            self._run_agent(state, "weather", self.weather_agent, WeatherAgentInput(
                city=req.destination, target_date=check_in.isoformat(),
            )),
        )

        if flight:
            state.flights = flight.data.flights
        if hotel:
            state.hotels = hotel.data.selected_hotels
        if activity:
            state.activities = activity.data.activities
            self._emit(state, "activity_reasoning", activity.data.reasoning)
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
        pick = max if state.strategy == "comfort" else min
        state.selected_flight = pick(state.flights, key=lambda f: f.price)
        state.selected_hotel = pick(state.hotels, key=lambda h: h.price_per_night)
        self._emit(
            state, "selection_made",
            f"strategy={state.strategy} flight={state.selected_flight.id} hotel={state.selected_hotel.id}",
        )

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
            max_hotel_price_per_night=hotel_cap(req),
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
            destination=req.destination, duration_days=req.duration_days,
            total_cost=state.budget_result.total, currency=req.currency, summary=summary,
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
        event = WorkflowEvent(run_id=state.run_id, event_type=event_type, message=message)
        state.events.append(event)
        logger.info("run=%s event=%s %s", state.run_id, event_type, message)
        if getattr(self, "_event_sink", None):
            self._event_sink(event)