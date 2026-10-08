# scripts/verify_system.py
"""Read-only verification of RAG + real agents. Run: python -m scripts.verify_system"""
import asyncio
from datetime import date
from decimal import Decimal

from app.agents.activity import ActivityAgent, ActivityAgentInput
from app.embeddings.local_provider import SentenceTransformerProvider
from app.llm.groq_provider import GroqProvider
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.orchestration.rules import (
    FOOD_PER_PERSON_PER_DAY,
    TRANSPORT_PER_PERSON_PER_DAY,
)
from app.schemas.state import TravelRequest
from app.services.retriever_service import RetrieverService

CITY = "Tokyo"  # must match the exact city value stored in document_chunks


def check(label: str, ok: bool) -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")


async def check_retrieval(retriever: RetrieverService) -> None:
    print("\n=== 1. Retrieval only (no LLM) ===")
    chunks = await retriever.retrieve("temples and traditional culture", city=CITY, top_k=3)
    check("retrieval returned chunks", len(chunks) > 0)
    for c in chunks:
        print(f"  score={c.score:.3f} source={c.source} | {c.content[:90]}...")
    check("scores sorted closest-first", [c.score for c in chunks] == sorted(c.score for c in chunks))

    other = await retriever.retrieve("temples", city="Atlantis", top_k=3)
    check("unknown city returns nothing (city filter works)", len(other) == 0)


async def check_activity_agent(llm, retriever: RetrieverService) -> None:
    print("\n=== 2. Activity Agent: with vs without RAG ===")
    inp = ActivityAgentInput(
        city=CITY, interests=["culture", "outdoor"], max_price=Decimal("5000"), preferences=None
    )
    without = await ActivityAgent(llm).run(inp)
    with_rag = await ActivityAgent(llm, retriever=retriever).run(inp)

    check("agent without RAG succeeded", without.success)
    check("agent with RAG succeeded", with_rag.success)
    if without.success and with_rag.success:
        ids_a = sorted(a.id for a in without.data.activities)
        ids_b = sorted(a.id for a in with_rag.data.activities)
        check("same tool facts regardless of RAG (RAG must not change data)", ids_a == ids_b)
        print("\n  WITHOUT RAG reasoning:\n  ", without.data.reasoning)
        print("\n  WITH RAG reasoning:\n  ", with_rag.data.reasoning)
        print("\n  -> Read both: the RAG one should mention destination context")
        print("     (e.g. real places/areas from your guide) but NO invented prices.")


async def check_full_run(llm) -> None:
    print("\n=== 3. Full orchestrator run (real LLM agents) ===")
    request = TravelRequest(
        origin="Delhi",
        destination=CITY,
        start_date=date(2026, 11, 20),
        travellers=2,
        duration_days=7,
        budget=Decimal("200000"),
        interests=["culture", "outdoor"],
    )
    orch = TravelOrchestrator.from_llm(llm, retry_delay=1.0)
    state = await orch.run(request)

    check("status is completed", state.status == "completed")
    check("flight selected", state.selected_flight is not None)
    check("hotel selected", state.selected_hotel is not None)
    check("flight came from tool results", state.selected_flight in state.flights)
    check("hotel came from tool results", state.selected_hotel in state.hotels)

    if state.selected_flight and state.selected_hotel and state.budget_result:
        days, n = request.duration_days, request.travellers
        expected = (
            state.selected_flight.price
            + state.selected_hotel.price_per_night * state.selected_hotel.nights
            + sum(a.price for a in state.activities)
            + TRANSPORT_PER_PERSON_PER_DAY * n * days
            + FOOD_PER_PERSON_PER_DAY * n * days
        )
        check(
            f"budget total matches independent recomputation ({state.budget_result.total} vs {expected})",
            Decimal(state.budget_result.total) == Decimal(expected),
        )
        check("passed flag consistent with total <= budget",
              state.budget_result.passed == (state.budget_result.total <= request.budget))

    check("replans within limit", state.iteration <= 3)
    print("\n  event trail:")
    for e in state.events:
        print(f"   {e.event_type:22s} {e.message[:80]}")
    print("\n  errors:", state.errors or "none")


async def main() -> None:
    llm = GroqProvider()
    retriever = RetrieverService(SentenceTransformerProvider())
    await check_retrieval(retriever)
    await check_activity_agent(llm, retriever)
    await check_full_run(llm)


if __name__ == "__main__":
    asyncio.run(main())