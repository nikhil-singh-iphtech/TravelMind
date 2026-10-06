from datetime import date
from decimal import Decimal

from app.agents import ActivityAgentOutput, BudgetAgent, ConstraintAgent, FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.orchestration.custom.replanner import Replanner
from app.schemas import Activity, Flight, Hotel
from app.schemas.state import TravelRequest
from tests.fakes import StubAgent
from app.schemas.weather import WeatherInfo

WEATHER = WeatherInfo(
    city="Tokyo", target_date=date(2026, 11, 1), temperature_celsius=22.0, condition="Clear"
)
FLIGHTS = [
    Flight(id="f1", airline="IndiGo", price=Decimal("64000")),
    Flight(id="f2", airline="Air India", price=Decimal("80000")),
]
HOTELS = [
    Hotel(id="h1", name="Central Inn", city="Tokyo", price_per_night=Decimal("6000"), nights=7),
    Hotel(id="h2", name="Riverside", city="Tokyo", price_per_night=Decimal("9000"), nights=7),
]
ACTIVITIES = [Activity(id="a1", name="Tour", price=Decimal("2500"))]


def make_request(budget: str) -> TravelRequest:
    return TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal(budget),
    )


def make_orchestrator() -> TravelOrchestrator:
    return TravelOrchestrator(
        flight_agent=StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
        replanner=Replanner(),
        retry_delay=0,
    )


async def test_over_budget_plan_recovers_after_switching_strategy():
    # Comfort picks f2(80000) + h2(9000x7=63000) = 143000 + extras -> over 150000.
    # Budget strategy picks f1(64000) + h1(6000x7=42000) = 106000 + extras -> fits.
    state = await make_orchestrator().run(make_request("150000"))

    assert state.status == "completed"
    assert state.iteration == 1
    assert state.strategy == "budget"
    assert state.selected_flight.id == "f1"
    assert state.selected_hotel.id == "h1"


async def test_events_include_a_replanning_entry():
    state = await make_orchestrator().run(make_request("150000"))

    types = [e.event_type for e in state.events]
    assert "replanning_started" in types


async def test_still_over_budget_gives_up_after_max_replans():
    # No combination of these candidates fits an absurdly small budget.
    state = await make_orchestrator().run(make_request("10000"))

    assert state.status == "failed"
    assert state.iteration == 3  # MAX_REPLANS, never exceeded
    assert "replan" in state.errors[-1].lower() or "constraints failed" in state.errors[-1].lower()


async def test_plan_that_fits_first_time_never_replans():
    state = await make_orchestrator().run(make_request("300000"))

    assert state.status == "completed"
    assert state.iteration == 0