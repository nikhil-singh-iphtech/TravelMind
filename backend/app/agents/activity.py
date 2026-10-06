from decimal import Decimal

from pydantic import BaseModel

from app.agents.base import AgentResult
from app.agents.tool_loop import GROUNDING_RULE, run_tool_loop
from app.llm.base import LLMProvider
from app.schemas.tools import ActivitySearchInput
from app.schemas.travel import Activity


class ActivityAgentInput(BaseModel):
    city: str
    interests: list[str] = []
    max_price: Decimal | None = None


class ActivityAgentOutput(BaseModel):
    activities: list[Activity]
    reasoning: str


class ActivityAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def run(self, input: ActivityAgentInput) -> AgentResult[ActivityAgentOutput]:
        interests = ", ".join(input.interests) if input.interests else "any"
        price_note = f" Max price per activity: {input.max_price}." if input.max_price else ""
        prompt = (
            f"Find activities in {input.city}. Interests: {interests}.{price_note} "
            f"Use the search_activities tool, then briefly explain which "
            f"activities you'd recommend and why. {GROUNDING_RULE}"
        )

        loop = await run_tool_loop(
            llm=self.llm,
            tool_name="search_activities",
            tool_description="Search for attractions and activities in a city, optionally filtered by interests and a maximum price.",
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