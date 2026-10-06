import asyncio
from datetime import date
from decimal import Decimal

from app.llm.groq_provider import GroqProvider
from app.orchestration.langgraph.graph import build_graph_from_llm, run_workflow
from app.schemas.state import TravelRequest


async def main():
    graph = build_graph_from_llm(GroqProvider())

    state = await run_workflow(
        graph,
        TravelRequest(
            origin="Delhi", destination="Tokyo", start_date=date(2026, 11, 1),
            travellers=2, duration_days=7, budget=Decimal("200000"),
            interests=["culture", "outdoor"],
        ),
    )

    print("\n--- EVENTS ---")
    for e in state.events:
        print(e.timestamp.strftime("%H:%M:%S"), e.event_type, "-", e.message)

    print("\n--- RESULT ---")
    print("status:", state.status)
    print("iteration:", state.iteration)
    if state.itinerary:
        print("itinerary:", state.itinerary.summary)


if __name__ == "__main__":
    asyncio.run(main())