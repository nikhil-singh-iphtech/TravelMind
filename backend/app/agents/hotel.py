from pydantic import BaseModel

from app.agents.base import AgentResult
from app.agents.tool_loop import GROUNDING_RULE, run_tool_loop
from app.llm.base import LLMProvider
from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel


class HotelAgentInput(BaseModel):
    city: str
    check_in: str  # ISO date string, kept as str at the agent boundary
    check_out: str
    guests: int
    max_price_per_night: float
    currency: str = "INR"


class HotelAgentOutput(BaseModel):
    selected_hotels: list[Hotel]
    reasoning: str


class HotelAgent:
    """
    Clear input: HotelAgentInput. Clear output: AgentResult[HotelAgentOutput].
    Limited tool: search_hotels. Does not touch budget or constraints.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def run(self, input: HotelAgentInput) -> AgentResult[HotelAgentOutput]:
        prompt = (
            f"Find hotel options in {input.city} for {input.guests} guests, "
            f"check-in {input.check_in}, check-out {input.check_out}, "
            f"max {input.max_price_per_night} {input.currency} per night. "
            f"Use the search_hotels tool, then briefly explain which hotels "
            f"you'd recommend and why. {GROUNDING_RULE}"
        )

        loop = await run_tool_loop(
            llm=self.llm,
            tool_name="search_hotels",
            tool_description=(
                "Search for hotels in a city for given check-in/check-out "
                "dates, guest count, and a maximum price per night."
            ),
            input_model=HotelSearchInput,
            prompt=prompt,
        )

        if loop.error:
            return AgentResult(success=False, error=loop.error)

        return AgentResult(
            success=True,
            data=HotelAgentOutput(
                selected_hotels=loop.tool_output,
                reasoning=loop.text or "Selected based on search results (no summary from model).",
            ),
        )