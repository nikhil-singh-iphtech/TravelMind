import asyncio
from datetime import date
from decimal import Decimal

from app.llm.groq_provider import GroqProvider
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.schemas.state import TravelRequest
from app.services.memory_service import MemoryService

USER_ID = 1  # from scripts/seed_demo_user.py output


async def main():
    memory = MemoryService()
    await memory.set_preference(USER_ID, "hotel_tier", "mid-range")
    await memory.set_preference(USER_ID, "transport", "prefers hotels near public transport")

    orchestrator = TravelOrchestrator.from_llm(GroqProvider(), memory_service=memory)

    state = await orchestrator.run(
        TravelRequest(
            origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
            travellers=2, duration_days=7, budget=Decimal("200000"),
        ),
        user_id=USER_ID,
    )

    print("status:", state.status)
    if state.itinerary:
        print("itinerary:", state.itinerary.summary)

    trips = await memory.get_recent_trips(USER_ID)
    print("\nrecent trips now on file:")
    for t in trips:
        print(" -", t.destination, "-", t.summary[:70])


if __name__ == "__main__":
    asyncio.run(main())