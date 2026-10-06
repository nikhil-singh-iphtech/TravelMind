import json
import logging
from typing import Type, TypeVar

from google import genai
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.schemas import ToolDefinition, ToolCallRequest, LLMToolResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_STRUCTURED_RETRIES = 3


class GeminiProvider(LLMProvider):
    def __init__(self):
        self._client = genai.Client(api_key=settings.llm_api_key)
        self._model = settings.llm_model or "gemini-2.0-flash"

    async def generate(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text

    async def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        schema_hint = json.dumps(schema.model_json_schema())
        full_prompt = (
            f"{prompt}\n\n"
            f"Respond with ONLY valid JSON matching this schema, "
            f"no explanation, no markdown fences:\n{schema_hint}"
        )

        last_error: Exception | None = None
        for attempt in range(MAX_STRUCTURED_RETRIES):
            raw = await self.generate(full_prompt)
            try:
                cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
                return schema.model_validate_json(cleaned)
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
        gemini_tools = [
            {
                "function_declarations": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                    for t in tools
                ]
            }
        ]

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[m["content"] for m in messages],
            config={"tools": gemini_tools},
        )

        candidate = response.candidates[0]
        tool_calls: list[ToolCallRequest] = []
        text_parts: list[str] = []

        for part in candidate.content.parts:
            if getattr(part, "function_call", None):
                tool_calls.append(
                    ToolCallRequest(
                        tool_name=part.function_call.name,
                        arguments=dict(part.function_call.args),
                    )
                )
            elif getattr(part, "text", None):
                text_parts.append(part.text)

        return LLMToolResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
        )