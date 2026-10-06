import time
from datetime import date
from decimal import Decimal

from app.agents import (
    ActivityAgentOutput, BudgetAgent, ConstraintAgent,
    FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput,
)
from app.orchestration.custom.orchestrator import TravelOrchestrator
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
ACTIVITIES = [
    Activity(id="a1", name="Tour", price=Decimal("2500")),
    Activity(id="a2", name="Food", price=Decimal("3500")),
]
WEATHER = WeatherInfo(
    city="Tokyo", target_date=date(2026, 11, 1), temperature_celsius=22.0, condition="Clear"
) 

class NoReplan:
    def should_replan(self, state) -> bool:
        return False

def make_request(budget: str = "200000") -> TravelRequest:
    return TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        start_date=date(2026, 11, 1),
        travellers=2,
        duration_days=7,
        budget=Decimal(budget),
    )


def make_orchestrator(flight=None, hotel=None, activity=None, weather=None, replanner=None) -> TravelOrchestrator:
    return TravelOrchestrator(
        flight_agent=flight or StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=hotel or StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=activity or StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=weather or StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
        replanner=replanner,
        retry_delay=0,
    )


async def test_happy_path_completes_with_itinerary():
    state = await make_orchestrator().run(make_request("200000"))

    # comfort strategy: flight 80000 + hotel 9000*7 + activities 6000
    # + food 2000*2*7 + transport 500*2*7 = 184000
    assert state.status == "completed"
    assert state.selected_flight.id == "f2"
    assert state.selected_hotel.id == "h2"
    assert state.budget_result.total == Decimal("184000")
    assert state.budget_result.passed is True
    assert state.itinerary is not None
    assert state.itinerary.total_cost == Decimal("184000")


async def test_over_budget_plan_fails_with_budget_violation():
    # Phase 8's orchestrator had no Replanner, so make_orchestrator() here
    # must build one explicitly WITHOUT a replanner to test this in isolation.
    state = await make_orchestrator(replanner=NoReplan()).run(make_request("150000"))

    assert state.status == "failed"
    assert state.budget_result.passed is False
    assert state.constraint_result.passed is False
    assert "budget" in {v.constraint for v in state.constraint_result.violations}
    assert state.itinerary is None

async def test_research_agents_run_in_parallel():
    def slow(data):
        return StubAgent(data, delay=0.2)

    orchestrator = make_orchestrator(
        flight=slow(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel=slow(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity=slow(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather=slow(WeatherAgentOutput(weather=WEATHER, summary="stub")),
    )

    start = time.perf_counter()
    state = await orchestrator.run(make_request())
    elapsed = time.perf_counter() - start

    assert state.status == "completed"
    # Sequential would take about 0.8s (4 x 0.2). Parallel takes about 0.2s.
    assert elapsed < 0.6


async def test_agent_is_retried_and_recovers():
    flight = StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub"), fail_times=2)

    state = await make_orchestrator(flight=flight).run(make_request())

    assert flight.calls == 3  # failed twice, succeeded on the third attempt
    assert state.status == "completed"


async def test_crashing_agent_is_retried_too():
    activity = StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub"), raise_times=1)

    state = await make_orchestrator(activity=activity).run(make_request())

    assert activity.calls == 2
    assert state.status == "completed"


async def test_essential_agent_failing_fails_the_run():
    flight = StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub"), fail_times=99)

    state = await make_orchestrator(flight=flight).run(make_request())

    assert flight.calls == 3  # gave up after MAX_AGENT_ATTEMPTS
    assert state.status == "failed"
    assert any("flight" in e for e in state.errors)


async def test_non_essential_agent_failing_does_not_fail_the_run():
    weather = StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub"), fail_times=99)

    state = await make_orchestrator(weather=weather).run(make_request())

    assert state.status == "completed"
    assert state.weather is None
    assert any("weather" in e for e in state.errors)


async def test_events_record_the_run_in_order():
    state = await make_orchestrator().run(make_request())

    types = [e.event_type for e in state.events]
    assert types[0] == "planning_started"
    assert types[-1] == "planning_completed"
    assert "budget_calculated" in types
    assert all(e.run_id == state.run_id for e in state.events)