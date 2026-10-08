# app/api/routes/travel_plans.py
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.models.user import User
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.orchestration.langgraph.graph import build_graph_from_llm, run_workflow
from app.schemas.api import PlanRequest, RefineRequest
from app.services.memory_service import MemoryService
from app.services.run_persistence_service import RunPersistenceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/travel-plans", tags=["travel-plans"])
_persistence = RunPersistenceService()


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def _get_llm():
    if settings.llm_provider.lower() == "gemini":
        return GeminiProvider()
    return GroqProvider()


@router.post("/stream")
async def stream_plan(
    body: PlanRequest,
    current_user: User | None = Depends(get_current_user),
) -> StreamingResponse:
    user_id = current_user.id if current_user else (body.user_id or 1)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        memory = MemoryService()
        llm = _get_llm()

        async def run_custom():
            try:
                orch = TravelOrchestrator.from_llm(llm, memory_service=memory)
                return await orch.run(
                    body.trip, user_id=user_id, event_sink=queue.put_nowait
                )
            finally:
                queue.put_nowait(None)  # ALWAYS end the stream

        async def run_langgraph():
            try:
                graph = build_graph_from_llm(llm)
                state = await run_workflow(
                    graph, body.trip, user_id=user_id, memory_service=memory
                )
                for event in state.events:
                    queue.put_nowait(event)
                return state
            finally:
                queue.put_nowait(None)

        runner = run_custom if body.engine == "custom" else run_langgraph
        task = asyncio.create_task(runner())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield _sse("progress", event.model_dump(mode="json"))

        try:
            state = await task
        except Exception as exc:
            # Log details server-side; send the client only a generic message.
            logger.error("run failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            yield _sse("error", {"message": "Planning failed. Please check parameters and try again."})
            return

        # Persist completed run to database
        if state and state.run_id:
            _persistence.save_run(
                run_id=state.run_id,
                user_id=user_id,
                request=body.trip,
                state=state,
            )

        yield _sse("complete", state.model_dump(mode="json"))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("", response_model=list[dict])
async def list_my_plans(current_user: User = Depends(get_current_user)):
    """List past planning runs for authenticated user."""
    return _persistence.list_user_runs(user_id=current_user.id)


@router.get("/public/{run_id}", response_model=dict)
async def get_public_plan(run_id: str):
    """Retrieve full details of a shareable planning run by run_id (unauthenticated)."""
    plan = _persistence.get_public_run(run_id=run_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found.",
        )
    return plan


@router.get("/{run_id}", response_model=dict)
async def get_plan(run_id: str, current_user: User = Depends(get_current_user)):
    """Retrieve full details of a specific planning run by run_id."""
    plan = _persistence.get_run(run_id=run_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found or access denied.",
        )
    return plan



@router.post("/{run_id}/refine", response_model=dict)
async def refine_plan(
    run_id: str,
    payload: "RefineRequest",
    current_user: User = Depends(get_current_user),
):
    """Interactively refine an existing plan by swapping flight, hotel, or activity selections."""
    from decimal import Decimal
    from app.core.budget import BudgetCalculator
    from app.core.constraints import ConstraintEngine
    from app.orchestration.rules import FOOD_PER_PERSON_PER_DAY, TRANSPORT_PER_PERSON_PER_DAY
    from app.schemas.api import RefineRequest
    from app.schemas.state import TravelRequest, TravelState

    plan = _persistence.get_run(run_id=run_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found or access denied.",
        )

    req = TravelRequest.model_validate(plan["request"])
    state = TravelState.model_validate(plan["result"])

    if payload.custom_budget is not None and payload.custom_budget > 0:
        req.budget = Decimal(str(payload.custom_budget))

    if payload.flight_id:
        selected_f = next((f for f in state.flights if f.id == payload.flight_id), None)
        if selected_f:
            state.selected_flight = selected_f

    if payload.hotel_id:
        selected_h = next((h for h in state.hotels if h.id == payload.hotel_id), None)
        if selected_h:
            state.selected_hotel = selected_h

    if payload.excluded_activity_ids:
        state.activities = [
            act for act in state.activities if act.id not in payload.excluded_activity_ids
        ]

    # Reevaluate Budget
    calc = BudgetCalculator()
    days, n = req.duration_days, req.travellers
    transport_tot = TRANSPORT_PER_PERSON_PER_DAY * n * days
    food_tot = FOOD_PER_PERSON_PER_DAY * n * days

    b_res = calc.calculate(
        budget=req.budget,
        flights=[state.selected_flight] if state.selected_flight else [],
        hotels=[state.selected_hotel] if state.selected_hotel else [],
        activities=state.activities,
        transport=transport_tot,
        food=food_tot,
    )
    state.budget_result = b_res

    # Reevaluate Constraints
    c_engine = ConstraintEngine()
    c_res = c_engine.check(
        total_cost=b_res.total,
        budget=req.budget,
        hotels=[state.selected_hotel] if state.selected_hotel else [],
        max_hotel_price_per_night=req.max_hotel_price_per_night,
        budget_currency=req.currency,
        travellers=req.travellers,
        expected_travellers=req.travellers,
        duration_days=req.duration_days,
        expected_duration_days=req.duration_days,
    )
    state.constraint_result = c_res
    state.status = "completed" if (b_res.passed and c_res.passed) else "failed"

    _persistence.save_run(
        run_id=run_id,
        user_id=current_user.id,
        request=req,
        state=state,
    )

    return _persistence.get_run(run_id=run_id, user_id=current_user.id)