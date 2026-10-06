import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_AGENT_ATTEMPTS = 3


async def run_agent_with_retry(
    *, run_id: str, name: str, agent: Any, agent_input: Any,
    delay: float = 1.0, max_attempts: int = MAX_AGENT_ATTEMPTS,
):
    """
    Runs one agent up to max_attempts times. Never raises: returns
    (result, None) on success, or (None, error_message) once attempts
    are exhausted. Shared by the custom orchestrator and the LangGraph
    nodes, so a flaky agent is retried the same way either way.
    """
    error = "unknown error"
    for attempt in range(1, max_attempts + 1):
        try:
            result = await agent.run(agent_input)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        else:
            if result.success:
                return result, None
            error = result.error or "unknown error"

        logger.warning(
            "run=%s agent=%s attempt=%d/%d error=%s", run_id, name, attempt, max_attempts, error,
        )
        if attempt < max_attempts:
            await asyncio.sleep(delay)

    return None, error