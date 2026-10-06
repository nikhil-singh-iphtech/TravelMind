from decimal import Decimal

import pytest
from pydantic import BaseModel

from app.core.config import settings
from app.llm.gemini_provider import GeminiProvider
from app.llm.schemas import ToolDefinition

pytestmark = pytest.mark.skipif(
    not settings.llm_api_key, reason="LLM_API_KEY not set — skipping live LLM tests"
)


class SimpleCity(BaseModel):
    name: str
    country: str


@pytest.mark.asyncio
async def test_generate_returns_text():
    provider = GeminiProvider()
    result = await provider.generate("Say the single word: hello")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_structured_returns_valid_model():
    provider = GeminiProvider()
    result = await provider.generate_structured(
        "Give me a well-known city in Japan.", SimpleCity
    )
    assert isinstance(result, SimpleCity)
    assert result.country.lower() == "japan"


@pytest.mark.asyncio
async def test_generate_with_tools_requests_correct_tool():
    provider = GeminiProvider()
    tools = [
        ToolDefinition(
            name="search_hotels",
            description="Search for hotels in a given city",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
    ]

    response = await provider.generate_with_tools(
        messages=[{"role": "user", "content": "Find me hotels in Tokyo"}],
        tools=tools,
    )

    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "search_hotels"
    assert "tokyo" in str(response.tool_calls[0].arguments).lower()