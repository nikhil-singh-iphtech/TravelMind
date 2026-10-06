import logging
from datetime import timedelta

from app.agents import (
    ActivityAgentInput, FlightAgentInput, HotelAgentInput, WeatherAgentInput,
)
from app.orchestration.agent_retry import run_agent_with_retry
from app.orchestration.custom.replanner import Replanner
from app.orchestration.langgraph.state import GraphState
from app.orchestration.rules import FOOD_PER_PERSON_PER_DAY, TRANSPORT_PER_PERSON_PER_DAY, hotel_cap
from app.schemas import Itinerary
from app.schemas.state import WorkflowEvent
from app.orchestration.custom.replanner import MAX_REPLANS

logger = logging.getLogger(__name__)

_replanner = Replanner()  # pure Python, reused as-is from Phase 9


# ----------------------------------------------------------------------
# Entry node — matches the first _emit() call at the top of run()
# ----------------------------------------------------------------------

async def start_node(state: GraphState) -> dict:
    event = WorkflowEvent(
        run_id=state.run_id, event_type="planning_started",
        message=f"Planning trip to {state.request.destination}",
    )
    return {"events": [event]}


# ----------------------------------------------------------------------
# Research nodes — one factory, reused for all four. Each wraps a
# Phase 7 agent exactly the way _run_agent did, via the SAME retry
# helper the custom orchestrator now uses too.
# ----------------------------------------------------------------------

def make_research_node(name: str, agent, build_input, extract):
    async def node(state: GraphState) -> dict:
        result, error = await run_agent_with_retry(
            run_id=state.run_id, name=name, agent=agent, agent_input=build_input(state),
        )
        if result is None:
            event = WorkflowEvent(
                run_id=state.run_id, event_type=f"{name}_failed", message=f"{name} agent failed: {error}",
            )
            return {"errors": [f"{name} agent failed: {error}"], "events": [event]}

        event = WorkflowEvent(run_id=state.run_id, event_type=f"{name}_completed", message=f"{name} agent completed")
        return {**extract(result.data), "events": [event]}

    return node


def _flight_input(state: GraphState) -> FlightAgentInput:
    req = state.request
    return FlightAgentInput(
        origin=req.origin, destination=req.destination,
        departure_date=req.start_date.isoformat(), travellers=req.travellers, currency=req.currency,
    )


def _hotel_input(state: GraphState) -> HotelAgentInput:
    req = state.request
    check_out = req.start_date + timedelta(days=req.duration_days)
    return HotelAgentInput(
        city=req.destination, check_in=req.start_date.isoformat(), check_out=check_out.isoformat(),
        guests=req.travellers, max_price_per_night=float(hotel_cap(req)), currency=req.currency,
    )


def _activity_input(state: GraphState) -> ActivityAgentInput:
    return ActivityAgentInput(city=state.request.destination, interests=state.request.interests)


def _weather_input(state: GraphState) -> WeatherAgentInput:
    return WeatherAgentInput(city=state.request.destination, target_date=state.request.start_date.isoformat())


# ----------------------------------------------------------------------
# Select — same Python rule as the custom orchestrator's _select
# ----------------------------------------------------------------------

async def select_node(state: GraphState) -> dict:
    if not state.flights or not state.hotels:
        event = WorkflowEvent(
            run_id=state.run_id, event_type="planning_failed",
            message="Cannot build a plan without flights and hotels",
        )
        return {
            "status": "failed",
            "errors": ["Cannot build a plan without flights and hotels"],
            "events": [event],
        }

    pick = max if state.strategy == "comfort" else min
    flight = pick(state.flights, key=lambda f: f.price)
    hotel = pick(state.hotels, key=lambda h: h.price_per_night)

    event = WorkflowEvent(
        run_id=state.run_id, event_type="selection_made",
        message=f"strategy={state.strategy} flight={flight.id} hotel={hotel.id}",
    )
    return {"selected_flight": flight, "selected_hotel": hotel, "events": [event]}


def route_after_select(state: GraphState) -> str:
    return "fail" if state.status == "failed" else "budget"


# ----------------------------------------------------------------------
# Budget / Constraint — same Python-decides-LLM-explains agents as before
# ----------------------------------------------------------------------

def make_budget_node(budget_agent):
    from app.agents import BudgetAgentInput

    async def node(state: GraphState) -> dict:
        req = state.request
        person_days = req.travellers * req.duration_days

        result = await budget_agent.run(BudgetAgentInput(
            budget=req.budget,
            flights=[state.selected_flight],
            hotels=[state.selected_hotel],
            activities=state.activities,
            transport=TRANSPORT_PER_PERSON_PER_DAY * person_days,
            food=FOOD_PER_PERSON_PER_DAY * person_days,
        ))
        br = result.data.result
        event_type = "budget_calculated" if br.passed else "budget_failed"
        event = WorkflowEvent(
            run_id=state.run_id, event_type=event_type,
            message=f"total={br.total} budget={br.budget} | {result.data.explanation}",
        )
        return {"budget_result": br, "events": [event]}

    return node


def make_constraint_node(constraint_agent):
    from app.agents import ConstraintAgentInput

    async def node(state: GraphState) -> dict:
        req = state.request
        result = await constraint_agent.run(ConstraintAgentInput(
            total_cost=state.budget_result.total,
            budget=req.budget,
            hotels=[state.selected_hotel],
            max_hotel_price_per_night=hotel_cap(req),
            travellers=req.travellers,
            expected_travellers=req.travellers,
            duration_days=state.selected_hotel.nights,
            expected_duration_days=req.duration_days,
        ))
        cr = result.data.result

        if cr.passed:
            event = WorkflowEvent(run_id=state.run_id, event_type="constraints_passed", message="All constraints satisfied")
        else:
            names = ", ".join(v.constraint for v in cr.violations)
            event = WorkflowEvent(run_id=state.run_id, event_type="constraints_failed", message=f"Violations: {names}")

        return {"constraint_result": cr, "events": [event]}

    return node


def route_after_constraints(state: GraphState) -> str:
    if state.constraint_result.passed:
        return "finish"
    if state.iteration < MAX_REPLANS:
        return "replan"
    return "fail"

# ----------------------------------------------------------------------
# Replan — reuses Phase 9's Replanner UNCHANGED. Key lesson: Replanner
# mutates the state object it's given, but LangGraph only tracks what a
# node RETURNS, not in-place mutation. So we diff events before/after
# and explicitly return everything the mutation touched.
# ----------------------------------------------------------------------

async def replan_node(state: GraphState) -> dict:
    events_before = len(state.events)
    _replanner.replan(state)  # mutates .iteration, .strategy, .request, appends one event
    new_events = state.events[events_before:]

    return {
        "iteration": state.iteration,
        "strategy": state.strategy,
        "request": state.request,
        "events": new_events,
    }


# ----------------------------------------------------------------------
# Finish / Fail
# ----------------------------------------------------------------------

async def finish_node(state: GraphState) -> dict:
    req = state.request
    summary = (
        f"{req.travellers} travellers, {req.duration_days} days in {req.destination}. "
        f"Flight: {state.selected_flight.airline}. Hotel: {state.selected_hotel.name}. "
        f"{len(state.activities)} activities. "
        f"Total {state.budget_result.total} of {req.budget} {req.currency}."
    )
    if state.weather:
        summary += f" Expected weather: {state.weather.condition}, {state.weather.temperature_celsius}°C."

    itinerary = Itinerary(
        destination=req.destination, duration_days=req.duration_days,
        total_cost=state.budget_result.total, currency=req.currency, summary=summary,
    )
    event = WorkflowEvent(run_id=state.run_id, event_type="planning_completed", message="Planning completed")
    return {"itinerary": itinerary, "status": "completed", "events": [event]}


async def fail_node(state: GraphState) -> dict:
    if state.status == "failed" and state.errors:
        reason = state.errors[-1]
    else:
        reason = f"Constraints failed after {state.iteration} replan(s)"

    event = WorkflowEvent(run_id=state.run_id, event_type="planning_failed", message=reason)
    return {"status": "failed", "errors": [reason], "events": [event]}