from datetime import date
from decimal import Decimal

from app.agents import ActivityAgentOutput, BudgetAgent, ConstraintAgent, FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.schemas import Activity, Flight, Hotel
from app.schemas.memory import Preference
from app.schemas.state import TravelRequest
from app.schemas.weather import WeatherInfo
from tests.fakes import FakeMemoryService, StubAgent

FLIGHTS = [Flight(id="f1", airline="IndiGo", price=Decimal("64000"))]
HOTELS = [Hotel(id="h1", name="Central Inn", city="Tokyo", price_per_night=Decimal("6000"), nights=7)]
ACTIVITIES = [Activity(id="a1", name="Tour", price=Decimal("2500"))]
WEATHER = WeatherInfo(city="Tokyo", target_date=date(2026, 11, 1), temperature_celsius=22.0, condition="Clear")


def make_request():
    return TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("300000"),
    )


def make_orchestrator(hotel=None, activity=None, flight=None, memory=None):
    return TravelOrchestrator(
        flight_agent=flight or StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=hotel or StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=activity or StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
        memory_service=memory,
        retry_delay=0,
    )


async def test_preferences_are_passed_into_hotel_and_activity_inputs():
    hotel = StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub"))
    activity = StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub"))
    memory = FakeMemoryService(preferences=[Preference(key="hotel_tier", value="mid-range")])

    await make_orchestrator(hotel=hotel, activity=activity, memory=memory).run(make_request(), user_id=1)

    assert "mid-range" in hotel.last_input.preferences
    assert "mid-range" in activity.last_input.preferences


async def test_completed_trip_is_saved_to_memory():
    memory = FakeMemoryService()

    state = await make_orchestrator(memory=memory).run(make_request(), user_id=1)

    assert state.status == "completed"
    assert len(memory.saved_trips) == 1
    assert memory.saved_trips[0][0] == 1


async def test_failed_trip_is_not_saved_to_memory():
    memory = FakeMemoryService()
    flight = StubAgent(FlightAgentOutput(flights=[], reasoning="stub"))  # no flights -> fails

    state = await make_orchestrator(flight=flight, memory=memory).run(make_request(), user_id=1)

    assert state.status == "failed"
    assert memory.saved_trips == []