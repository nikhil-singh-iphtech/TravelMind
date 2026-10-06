import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.llm.groq_provider import GroqProvider
from app.orchestration.custom.orchestrator import TravelOrchestrator
from app.orchestration.langgraph.graph import build_graph_from_llm, run_workflow
from app.schemas.api import PlanRequest
from app.services.memory_service import MemoryService

router = APIRouter()


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/travel-plans/stream")
async def stream_travel_plan(body: PlanRequest):
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        memory = MemoryService()
        llm = GroqProvider()

        async def run_custom():
            # event_sink pushes each event onto the queue the INSTANT
            # _emit fires, not after the run finishes — true streaming.
            orchestrator = TravelOrchestrator.from_llm(llm, memory_service=memory)
            state = await orchestrator.run(
                body.trip, user_id=body.user_id, event_sink=queue.put_nowait,
            )
            await queue.put(None)  # sentinel: no more events
            return state

        async def run_langgraph():
            # Simplification for this phase: run to completion, then
            # replay the stored events — not truly live. See Step 4.
            graph = build_graph_from_llm(llm)
            state = await run_workflow(graph, body.trip, user_id=body.user_id, memory_service=memory)
            for event in state.events:
                await queue.put(event)
            await queue.put(None)
            return state

        runner = run_custom if body.engine == "custom" else run_langgraph
        task = asyncio.create_task(runner())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield _sse("progress", event.model_dump(mode="json"))

        state = await task
        yield _sse("complete", state.model_dump(mode="json"))

    return StreamingResponse(event_generator(), media_type="text/event-stream")