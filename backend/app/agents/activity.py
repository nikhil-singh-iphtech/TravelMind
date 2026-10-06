from decimal import Decimal

from pydantic import BaseModel

from app.agents.base import AgentResult
from app.agents.tool_loop import GROUNDING_RULE, run_tool_loop
from app.llm.base import LLMProvider
from app.schemas.tools import ActivitySearchInput
from app.schemas.travel import Activity
from app.services.retriever_service import RetrieverService


class ActivityAgentInput(BaseModel):
    city: str
    interests: list[str] = []
    max_price: Decimal | None = None
    preferences: str | None = None  # e.g. "prefers cultural activities"


class ActivityAgentOutput(BaseModel):
    activities: list[Activity]
    reasoning: str


class ActivityAgent:
    def __init__(self, llm: LLMProvider, retriever: RetrieverService | None = None):
        self.llm = llm
        self.retriever = retriever

    async def run(self, input: ActivityAgentInput) -> AgentResult[ActivityAgentOutput]:
        interests = ", ".join(input.interests) if input.interests else "any"
        price_note = f" Max price per activity: {input.max_price}." if input.max_price else ""

        context_block = ""
        if self.retriever is not None:
            query = f"{input.city} {interests}".strip()
            retrieved = await self.retriever.retrieve(query=query, city=input.city, top_k=3)
            if retrieved:
                context_block = (
                    "\n\nBackground context about the destination (for flavor and "
                    "explaining WHY an activity fits — NOT a source of prices or "
                    "availability; those come only from the tool):\n"
                    + "\n".join(f"- {c.content}" for c in retrieved)
                )

        preferences_block = (
            f"\n\nStated user preferences (use these to decide which activities "
            f"to emphasize — do not let them override or invent data the tool "
            f"didn't return): {input.preferences}"
            if input.preferences else ""
        )

        prompt = (
            f"Find activities in {input.city}. Interests: {interests}.{price_note} "
            f"Use the search_activities tool, then briefly explain which "
            f"activities you'd recommend and why. {GROUNDING_RULE}"
            f"{context_block}{preferences_block}"
        )

        loop = await run_tool_loop(
            llm=self.llm,
            tool_name="search_activities",
            tool_description=(
                "Search for attractions and activities in a city, optionally "
                "filtered by interests and a maximum price."
            ),
            input_model=ActivitySearchInput,
            prompt=prompt,
        )

        if loop.error:
            return AgentResult(success=False, error=loop.error)

        return AgentResult(
            success=True,
            data=ActivityAgentOutput(
                activities=loop.tool_output,
                reasoning=loop.text or "Selected based on search results (no summary from model).",
            ),
        )