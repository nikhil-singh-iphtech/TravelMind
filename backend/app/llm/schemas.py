from typing import Any

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """
    Describes one callable tool to the LLM: its name, a natural
    language description (so the model knows *when* to use it),
    and the JSON schema of its expected input.
    """
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema, typically from a Pydantic model


class ToolCallRequest(BaseModel):
    """
    What the model hands back when it decides to call a tool,
    instead of (or alongside) replying with plain text.
    """
    tool_name: str
    arguments: dict[str, Any]


class LLMToolResponse(BaseModel):
    """
    Result of generate_with_tools(): either the model replied with
    text, or it requested one or more tool calls. Never both being
    None — text is None if a tool call is present, and vice versa.
    """
    text: str | None = None
    tool_calls: list[ToolCallRequest] = []