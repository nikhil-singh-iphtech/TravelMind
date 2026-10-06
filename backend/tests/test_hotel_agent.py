import pytest
from pydantic import BaseModel

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.schemas import ToolDefinition, ToolCallRequest, LLMToolResponse
from app.agents.hotel import HotelAgent, HotelAgentInput


class FakeToolCallingProvider(LLMProvider):
    """
    A fake LLMProvider that always requests search_hotels once, then
    returns a text summary. Lets us test the agent's loop, tool
    dispatch, and result handling without hitting a real API.
    """

    def __init__(self):
        self._calls = 0

    async def generate(self, prompt: str) -> str:
        return "not used in this test"

    async def generate_structured(self, prompt: str, schema):
        raise NotImplementedError

    async def generate_with_tools(
        self, messages: list[dict], tools: list[ToolDefinition]
    ) -> LLMToolResponse:
        self._calls += 1
        if self._calls == 1:
            return LLMToolResponse(
                tool_calls=[
                    ToolCallRequest(
                        tool_name="search_hotels",
                        arguments={
                            "city": "Tokyo",
                            "check_in": "2026-11-01",
                            "check_out": "2026-11-08",
                            "guests": 2,
                            "max_price_per_night": "10000",
                        },
                    )
                ]
            )
        return LLMToolResponse(text="I recommend the mid-range option.")


@pytest.mark.asyncio
async def test_hotel_agent_completes_full_loop_with_fake_provider():
    agent = HotelAgent(llm=FakeToolCallingProvider())

    result = await agent.run(
        HotelAgentInput(
            city="Tokyo",
            check_in="2026-11-01",
            check_out="2026-11-08",
            guests=2,
            max_price_per_night=10000.0,
        )
    )

    assert result.success is True
    assert len(result.data.selected_hotels) > 0
    assert result.data.reasoning == "I recommend the mid-range option."


pytestmark_live = pytest.mark.skipif(
    not settings.llm_api_key, reason="LLM_API_KEY not set — skipping live LLM test"
)


@pytestmark_live
@pytest.mark.asyncio
async def test_hotel_agent_with_real_gemini_provider():
    from app.llm.gemini_provider import GeminiProvider

    agent = HotelAgent(llm=GeminiProvider())

    result = await agent.run(
        HotelAgentInput(
            city="Tokyo",
            check_in="2026-11-01",
            check_out="2026-11-08",
            guests=2,
            max_price_per_night=12000.0,
        )
    )

    assert result.success is True
    assert len(result.data.selected_hotels) > 0