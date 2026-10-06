import logging
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AgentResult(BaseModel, Generic[T]):
    """
    Shared result wrapper every agent returns. Keeps output
    structured and makes failures explicit instead of raising
    exceptions that callers have to remember to catch.
    """

    success: bool
    data: T | None = None
    error: str | None = None


async def explain_result(llm: LLMProvider | None, result: BaseModel) -> str:
    """
    Ask the LLM to put an already-decided result into words.

    The verdict (passed / failed, totals) was computed by Python before
    this is called. If the LLM is missing or fails, we fall back to the
    raw result, so the verdict never depends on the model being available.
    """
    fallback = result.model_dump_json()
    if llm is None:
        return fallback

    prompt = (
        "In two short sentences, explain this result to a traveller. "
        "Use ONLY the numbers and fields given. Do not add, change, or "
        "recalculate any number.\n\n" + fallback
    )
    try:
        return await llm.generate(prompt)
    except Exception as exc:  # LLM failure must never change the verdict
        logger.warning("explain_result failed, using raw result: %s", exc)
        return fallback