from pydantic import BaseModel

from app.agents.base import AgentResult
from app.agents.tool_loop import GROUNDING_RULE, run_tool_loop
from app.llm.base import LLMProvider
from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo


class WeatherAgentInput(BaseModel):
    city: str
    target_date: str  # ISO date string


class WeatherAgentOutput(BaseModel):
    weather: WeatherInfo
    summary: str


class WeatherAgent:
    """Weather comes ONLY from the tool. The model just summarises it."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def run(self, input: WeatherAgentInput) -> AgentResult[WeatherAgentOutput]:
        prompt = (
            f"Get the weather for {input.city} on {input.target_date}. Use the "
            f"get_weather tool, then summarise it in one sentence for a traveller. "
            f"{GROUNDING_RULE}"
        )

        loop = await run_tool_loop(
            llm=self.llm,
            tool_name="get_weather",
            tool_description="Get the weather for a city on a specific date.",
            input_model=WeatherInput,
            prompt=prompt,
        )

        if loop.error:
            return AgentResult(success=False, error=loop.error)

        return AgentResult(
            success=True,
            data=WeatherAgentOutput(
                weather=loop.tool_output,
                summary=loop.text or "Weather retrieved (no summary from model).",
            ),
        )