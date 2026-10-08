# scripts/inspect_currency.py
"""Prints what currencies/prices the selected offers actually have. Run: python -m scripts.inspect_currency"""
import asyncio
from datetime import date
from decimal import Decimal

from app.llm.groq_provider import GroqProvider
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.schemas.state import TravelRequest


async def main() -> None:
    request = TravelRequest(
        origin="Delhi", destination="Tokyo", start_date=date(2026, 10, 20),
        travellers=2, duration_days=7, budget=Decimal("130000"),
        interests=["culture", "outdoor"],
    )
    state = await TravelOrchestrator.from_llm(GroqProvider(), retry_delay=1.0).run(request)

    print("\nFLIGHTS")
    for f in state.flights:
        print(f"  {f.id} {f.airline} price={f.price} currency={f.currency}")
    print("\nHOTELS")
    for h in state.hotels:
        print(f"  {h.id} {h.name} per_night={h.price_per_night} nights={h.nights} "
              f"total={h.total_price} currency={h.currency}")
    print("\nselected flight:", state.selected_flight.id if state.selected_flight else None)
    print("selected hotel:", state.selected_hotel.id if state.selected_hotel else None)
    print("weather:", state.weather)
    print("\nreplans:", state.iteration, "| status:", state.status)
    print("budget:", state.budget_result)
    for e in state.events:
        print(f"  {e.event_type:20s} {e.message[:90]}")


asyncio.run(main())