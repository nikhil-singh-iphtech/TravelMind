import asyncio

from app.db.models.past_trip import PastTrip
from app.db.models.user_preference import UserPreference
from app.db.session import SessionLocal
from app.schemas.memory import Preference, TripRecord
from app.schemas.state import TravelState


class MemoryService:
    """
    Structured memory, not RAG — plain SQL lookups by user_id, no
    embeddings. Preferences are short, explicit facts; a WHERE clause
    is all that's needed. DB calls are sync, so each one is wrapped in
    asyncio.to_thread, same pattern as RetrieverService.
    """

    async def get_preferences(self, user_id: int) -> list[Preference]:
        return await asyncio.to_thread(self._get_preferences_sync, user_id)

    def _get_preferences_sync(self, user_id: int) -> list[Preference]:
        with SessionLocal() as session:
            rows = session.query(UserPreference).filter(UserPreference.user_id == user_id).all()
            return [Preference(key=r.key, value=r.value) for r in rows]

    async def set_preference(self, user_id: int, key: str, value: str) -> None:
        await asyncio.to_thread(self._set_preference_sync, user_id, key, value)

    def _set_preference_sync(self, user_id: int, key: str, value: str) -> None:
        with SessionLocal() as session:
            existing = (
                session.query(UserPreference)
                .filter(UserPreference.user_id == user_id, UserPreference.key == key)
                .first()
            )
            if existing:
                existing.value = value
            else:
                session.add(UserPreference(user_id=user_id, key=key, value=value))
            session.commit()

    async def save_trip(self, user_id: int, state: TravelState) -> None:
        await asyncio.to_thread(self._save_trip_sync, user_id, state)

    def _save_trip_sync(self, user_id: int, state: TravelState) -> None:
        itinerary = state.itinerary
        with SessionLocal() as session:
            session.add(PastTrip(
                user_id=user_id,
                destination=itinerary.destination,
                start_date=state.request.start_date,
                duration_days=itinerary.duration_days,
                travellers=state.request.travellers,
                total_cost=itinerary.total_cost,
                currency=itinerary.currency,
                summary=itinerary.summary,
            ))
            session.commit()

    async def get_recent_trips(self, user_id: int, limit: int = 5) -> list[TripRecord]:
        return await asyncio.to_thread(self._get_recent_trips_sync, user_id, limit)

    def _get_recent_trips_sync(self, user_id: int, limit: int) -> list[TripRecord]:
        with SessionLocal() as session:
            rows = (
                session.query(PastTrip)
                .filter(PastTrip.user_id == user_id)
                .order_by(PastTrip.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                TripRecord(
                    destination=r.destination, start_date=r.start_date, duration_days=r.duration_days,
                    travellers=r.travellers, total_cost=r.total_cost, currency=r.currency,
                    summary=r.summary, created_at=r.created_at,
                )
                for r in rows
            ]