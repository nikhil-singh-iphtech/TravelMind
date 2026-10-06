from datetime import date
from decimal import Decimal

from app.agents import ActivityAgentOutput, BudgetAgent, ConstraintAgent, FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput
from app.orchestration.langgraph.graph import build_graph, run_workflow
from app.schemas import Activity, Flight, Hotel
from app.schemas.state import TravelRequest
from app.schemas.weather import WeatherInfo
from tests.fakes import StubAgent

FLIGHTS = [
    Flight(id="f1", airline="IndiGo", price=Decimal("64000")),
    Flight(id="f2", airline="Air India", price=Decimal("80000")),
]
HOTELS = [
    Hotel(id="h1", name="Central Inn", city="Tokyo", price_per_night=Decimal("6000"), nights=7),
    Hotel(id="h2", name="Riverside", city="Tokyo", price_per_night=Decimal("9000"), nights=7),
]
ACTIVITIES = [Activity(id="a1", name="Tour", price=Decimal("2500"))]
WEATHER = WeatherInfo(city="Tokyo", target_date=date(2026, 11, 1), temperature_celsius=22.0, condition="Clear")


def make_request(budget: str) -> TravelRequest:
    return TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal(budget),
    )


def make_graph(flight=None, hotel=None):
    return build_graph(
        flight_agent=flight or StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=hotel or StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
    )


async def test_happy_path_completes_with_itinerary():
    state = await run_workflow(make_graph(), make_request("200000"))

    assert state.status == "completed"
    assert state.selected_flight.id == "f2"
    assert state.selected_hotel.id == "h2"
    assert state.budget_result.passed is True
    assert state.itinerary is not None


async def test_over_budget_plan_recovers_via_replan():
    state = await run_workflow(make_graph(), make_request("150000"))

    assert state.status == "completed"
    assert state.iteration == 1
    assert state.strategy == "budget"
    assert state.selected_flight.id == "f1"


async def test_still_over_budget_gives_up_after_max_replans():
    state = await run_workflow(make_graph(), make_request("10000"))

    assert state.status == "failed"
    assert state.iteration == 3


async def test_events_accumulate_from_all_four_parallel_nodes():
    """
    The reducer test: if Annotated[list, operator.add] were missing on
    `events`, only one of the four research nodes' events would survive.
    """
    state = await run_workflow(make_graph(), make_request("200000"))

    types = {e.event_type for e in state.events}
    assert "flight_completed" in types
    assert "hotel_completed" in types
    assert "activity_completed" in types
    assert "weather_completed" in types


async def test_essential_agent_failing_fails_the_run():
    flight = StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub"), fail_times=99)

    state = await run_workflow(make_graph(flight=flight), make_request("200000"))

    assert flight.calls == 3
    assert state.status == "failed"