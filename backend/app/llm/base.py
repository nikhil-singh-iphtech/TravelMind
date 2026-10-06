from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

from app.llm.schemas import ToolDefinition, LLMToolResponse

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """
    Abstract interface every LLM provider implements. Code that
    needs an LLM should depend on this type, not a specific
    provider — swapping providers later means writing one new
    class, not touching every caller.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Plain text generation."""
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """
        Generation constrained to a Pydantic schema. Must return a
        validated instance of `schema` or raise after retries are
        exhausted — never a best-effort unvalidated dict.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_with_tools(
        self, messages: list[dict], tools: list[ToolDefinition]
    ) -> LLMToolResponse:
        """
        Gives the model a list of available tools and lets it
        decide whether to respond with text or request a tool call.
        The provider does NOT execute the tool — it only reports
        what the model wants called.
        """
        raise NotImplementedError