import json
import logging
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMProvider
from app.llm.schemas import ToolDefinition
from app.tools.registry import TOOLS

logger = logging.getLogger(__name__)

MAX_TOOL_LOOPS = 3

# Shared by every agent prompt. Added after the model invented hotel
# amenities that were not in the tool data.
GROUNDING_RULE = (
    "Base your answer ONLY on the fields returned by the tool. "
    "Do not invent amenities, ratings, reviews, locations, or any "
    "other detail that is not in the tool result."
)


class ToolLoopResult(BaseModel):
    """What the loop hands back: tool data + model text, or an error."""

    tool_output: Any = None
    text: str | None = None
    error: str | None = None


def _to_jsonable(output: Any) -> Any:
    """Turn a tool's Pydantic output (one object or a list) into plain JSON data."""
    if isinstance(output, list):
        return [item.model_dump(mode="json") for item in output]
    return output.model_dump(mode="json")


async def run_tool_loop(
    *,
    llm: LLMProvider,
    tool_name: str,
    tool_description: str,
    input_model: Type[BaseModel],
    prompt: str,
) -> ToolLoopResult:
    """
    The tool-calling loop shared by all LLM agents.

    1. Offer ONE tool to the model (schema generated from input_model).
    2. If the model requests it, validate its arguments with input_model.
    3. Execute via the TOOLS registry.
    4. Feed the result back and let the model write its final answer.

    Gives up after MAX_TOOL_LOOPS so it can never loop forever.
    """
    tool_def = ToolDefinition(
        name=tool_name,
        description=tool_description,
        parameters=input_model.model_json_schema(),
    )
    messages = [{"role": "user", "content": prompt}]
    tool_output: Any = None

    for _ in range(MAX_TOOL_LOOPS):
        response = await llm.generate_with_tools(messages=messages, tools=[tool_def])

        if not response.tool_calls:
            if tool_output is None:
                return ToolLoopResult(
                    error=f"Model responded without calling {tool_name}"
                )
            return ToolLoopResult(tool_output=tool_output, text=response.text)

        for call in response.tool_calls:
            if call.tool_name != tool_name:
                logger.warning("Unexpected tool requested: %s", call.tool_name)
                continue

            try:
                validated = input_model.model_validate(call.arguments)
            except ValidationError as exc:
                logger.warning("tool=%s status=invalid_arguments error=%s", tool_name, exc)
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your {tool_name} arguments were invalid: {exc}. "
                            f"Please try again with valid arguments."
                        ),
                    }
                )
                continue

            tool_output = await TOOLS[tool_name](validated)
            logger.info("tool=%s status=completed", tool_name)

            messages.append(
                {
                    "role": "user",
                    "content": f"{tool_name} returned: {json.dumps(_to_jsonable(tool_output))}",
                }
            )

    if tool_output is not None:
        return ToolLoopResult(tool_output=tool_output, text=None)

    return ToolLoopResult(error=f"{tool_name} loop exceeded {MAX_TOOL_LOOPS} attempts without results")