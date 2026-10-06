import json
import logging
from typing import Type, TypeVar

from groq import AsyncGroq
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.schemas import ToolDefinition, ToolCallRequest, LLMToolResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_STRUCTURED_RETRIES = 3


class GroqProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model or "llama-3.3-70b-versatile"

    async def generate(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        schema_hint = json.dumps(schema.model_json_schema())
        full_prompt = (
            f"{prompt}\n\n"
            f"Respond with ONLY valid JSON matching this schema, "
            f"no explanation, no markdown fences:\n{schema_hint}"
        )

        last_error: Exception | None = None
        for attempt in range(MAX_STRUCTURED_RETRIES):
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": full_prompt}],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            try:
                return schema.model_validate_json(raw)
            except (ValidationError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "generate_structured attempt %d/%d failed: %s",
                    attempt + 1, MAX_STRUCTURED_RETRIES, exc,
                )

        raise ValueError(
            f"LLM failed to produce valid {schema.__name__} after "
            f"{MAX_STRUCTURED_RETRIES} attempts: {last_error}"
        )

    async def generate_with_tools(
        self, messages: list[dict], tools: list[ToolDefinition]
    ) -> LLMToolResponse:
        groq_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

        groq_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=groq_messages,
            tools=groq_tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        tool_calls: list[ToolCallRequest] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCallRequest(
                        tool_name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return LLMToolResponse(
            text=message.content,
            tool_calls=tool_calls,
        )