from pydantic import BaseModel

from app.agents.base import AgentResult
from app.agents.tool_loop import GROUNDING_RULE, run_tool_loop
from app.llm.base import LLMProvider
from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight


class FlightAgentInput(BaseModel):
    origin: str
    destination: str
    departure_date: str  # ISO date string
    travellers: int
    currency: str = "INR"


class FlightAgentOutput(BaseModel):
    flights: list[Flight]
    reasoning: str


class FlightAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def run(self, input: FlightAgentInput) -> AgentResult[FlightAgentOutput]:
        prompt = (
            f"Find flights from {input.origin} to {input.destination} departing "
            f"{input.departure_date} for {input.travellers} travellers, prices in "
            f"{input.currency}. Use the search_flights tool, then briefly explain "
            f"which flight you'd recommend and why. {GROUNDING_RULE}"
        )

        loop = await run_tool_loop(
            llm=self.llm,
            tool_name="search_flights",
            tool_description="Search for flights between two cities on a departure date for a number of travellers.",
            input_model=FlightSearchInput,
            prompt=prompt,
        )

        if loop.error:
            return AgentResult(success=False, error=loop.error)

        return AgentResult(
            success=True,
            data=FlightAgentOutput(
                flights=loop.tool_output,
                reasoning=loop.text or "Selected based on search results (no summary from model).",
            ),
        )