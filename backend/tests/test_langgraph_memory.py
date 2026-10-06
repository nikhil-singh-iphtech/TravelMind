from datetime import date
from decimal import Decimal

from app.agents import ActivityAgentOutput, BudgetAgent, ConstraintAgent, FlightAgentOutput, HotelAgentOutput, WeatherAgentOutput
from app.orchestration.langgraph.graph import build_graph, run_workflow
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


def make_graph(hotel=None, activity=None):
    return build_graph(
        flight_agent=StubAgent(FlightAgentOutput(flights=FLIGHTS, reasoning="stub")),
        hotel_agent=hotel or StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub")),
        activity_agent=activity or StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub")),
        weather_agent=StubAgent(WeatherAgentOutput(weather=WEATHER, summary="stub")),
        budget_agent=BudgetAgent(llm=None),
        constraint_agent=ConstraintAgent(llm=None),
    )


async def test_preferences_flow_into_hotel_and_activity_inputs():
    hotel = StubAgent(HotelAgentOutput(selected_hotels=HOTELS, reasoning="stub"))
    activity = StubAgent(ActivityAgentOutput(activities=ACTIVITIES, reasoning="stub"))
    memory = FakeMemoryService(preferences=[Preference(key="hotel_tier", value="mid-range")])

    await run_workflow(make_graph(hotel=hotel, activity=activity), make_request(), user_id=1, memory_service=memory)

    assert "mid-range" in hotel.last_input.preferences
    assert "mid-range" in activity.last_input.preferences


async def test_completed_trip_is_saved_to_memory():
    memory = FakeMemoryService()

    state = await run_workflow(make_graph(), make_request(), user_id=1, memory_service=memory)

    assert state.status == "completed"
    assert len(memory.saved_trips) == 1