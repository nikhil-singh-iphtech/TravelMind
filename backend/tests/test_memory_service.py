from datetime import date
from decimal import Decimal

import pytest

from app.db.models.past_trip import PastTrip
from app.db.models.user import User
from app.db.models.user_preference import UserPreference
from app.db.session import SessionLocal
from app.schemas.results import Itinerary
from app.schemas.state import TravelRequest, TravelState
from app.services.memory_service import MemoryService


@pytest.fixture
def test_user_id():
    with SessionLocal() as session:
        user = User(email="test_memory@example.com", full_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)
        uid = user.id
    yield uid
    with SessionLocal() as session:
        session.query(PastTrip).filter(PastTrip.user_id == uid).delete()
        session.query(UserPreference).filter(UserPreference.user_id == uid).delete()
        session.query(User).filter(User.id == uid).delete()
        session.commit()


@pytest.fixture
def memory():
    return MemoryService()


async def test_set_and_get_preferences(memory, test_user_id):
    await memory.set_preference(test_user_id, "hotel_tier", "mid-range")
    await memory.set_preference(test_user_id, "transport", "public transport")

    prefs = await memory.get_preferences(test_user_id)

    values = {p.key: p.value for p in prefs}
    assert values["hotel_tier"] == "mid-range"
    assert values["transport"] == "public transport"


async def test_set_preference_updates_existing_key(memory, test_user_id):
    await memory.set_preference(test_user_id, "hotel_tier", "budget")
    await memory.set_preference(test_user_id, "hotel_tier", "luxury")

    prefs = await memory.get_preferences(test_user_id)
    matching = [p for p in prefs if p.key == "hotel_tier"]

    assert len(matching) == 1
    assert matching[0].value == "luxury"


async def test_save_trip_and_get_recent_trips(memory, test_user_id):
    request = TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
        travellers=2, duration_days=7, budget=Decimal("200000"),
    )
    state = TravelState(request=request, status="completed")
    state.itinerary = Itinerary(
        destination="Tokyo", duration_days=7, total_cost=Decimal("184000"),
        currency="INR", summary="A great trip to Tokyo.",
    )

    await memory.save_trip(test_user_id, state)
    trips = await memory.get_recent_trips(test_user_id, limit=5)

    assert len(trips) == 1
    assert trips[0].destination == "Tokyo"
    assert trips[0].total_cost == Decimal("184000")