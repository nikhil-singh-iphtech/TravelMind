import asyncio

from app.agents.base import AgentResult
from app.llm.base import LLMProvider
from app.llm.schemas import LLMToolResponse, ToolCallRequest


class FakeToolProvider(LLMProvider):
    """
    A scriptable fake LLM.

    - arguments=None  -> the model never calls the tool (just replies with text)
    - arguments={...} -> the model requests the tool once, then replies with text
    """

    def __init__(self, tool_name: str = "", arguments: dict | None = None, final_text: str = "Done."):
        self.tool_name = tool_name
        self.arguments = arguments
        self.final_text = final_text
        self._calls = 0

    async def generate(self, prompt: str) -> str:
        return "Fake explanation."

    async def generate_structured(self, prompt: str, schema):
        raise NotImplementedError

    async def generate_with_tools(self, messages, tools) -> LLMToolResponse:
        self._calls += 1
        if self.arguments is not None and self._calls == 1:
            return LLMToolResponse(
                tool_calls=[ToolCallRequest(tool_name=self.tool_name, arguments=self.arguments)]
            )
        return LLMToolResponse(text=self.final_text)


class StubAgent:
    """
    Stands in for a whole agent inside orchestrator tests.

    - fail_times:  first N calls return success=False
    - raise_times: first N calls raise an exception
    - delay:       seconds to sleep per call (to prove parallel execution)
    """

    def __init__(self, data, *, fail_times: int = 0, raise_times: int = 0, delay: float = 0.0):
        self.data = data
        self.fail_times = fail_times
        self.raise_times = raise_times
        self.delay = delay
        self.calls = 0

    async def run(self, input):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.calls <= self.raise_times:
            raise RuntimeError("stub crashed")
        if self.calls <= self.raise_times + self.fail_times:
            return AgentResult(success=False, error="stub failure")
        return AgentResult(success=True, data=self.data)