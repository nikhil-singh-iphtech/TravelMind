from datetime import date
from decimal import Decimal

from app.agents import ActivityAgentOutput, BudgetAgent, ConstraintAgent, FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.schemas import Activity, Flight, Hotel
from app.schemas.state import TravelRequest
from app.schemas.weather import WeatherInfo
from tests.fakes import StubAgent

FLIGHTS = [Flight(id="f1", airline="IndiGo", price=Decimal("64000"))]
HOTELS = [Hotel(id="h1", name="Central Inn", city="Tokyo", price_per_night=Decimal("6000"), nights=7)]
ACTIVITIES = [Activity(id="a1", name="Tour", price=Decimal("2500"))]
WEATHER = WeatherInfo(city="Tokyo", target_date=date(2026, 11, 1), temperature_celsius=22.0, condition="Clear")


def make_orchestrator():
    return TravelOrchestrator(
        flight_agent=StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
        retry_delay=0,
    )


def make_request():
    return TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("300000"),
    )


async def test_event_sink_receives_every_event_as_it_happens():
    received = []

    state = await make_orchestrator().run(make_request(), event_sink=received.append)

    assert state.status == "completed"
    assert len(received) == len(state.events)
    assert [e.event_type for e in received] == [e.event_type for e in state.events]


async def test_orchestrator_still_works_without_an_event_sink():
    state = await make_orchestrator().run(make_request())  # no event_sink passed

    assert state.status == "completed"