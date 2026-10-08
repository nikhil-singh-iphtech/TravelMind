from decimal import Decimal

from pydantic import BaseModel

from app.agents.base import AgentResult, explain_result
from app.core.constraints import ConstraintEngine
from app.llm.base import LLMProvider
from app.schemas import ConstraintResult, Hotel


class ConstraintAgentInput(BaseModel):
    total_cost: Decimal
    budget: Decimal
    hotels: list[Hotel]
    max_hotel_price_per_night: Decimal | None = None
    budget_currency: str = "INR"
    travellers: int
    expected_travellers: int
    duration_days: int
    expected_duration_days: int


class ConstraintAgentOutput(BaseModel):
    result: ConstraintResult
    explanation: str


class ConstraintAgent:
    """Python checks the constraints. The LLM (optional) only explains the outcome."""

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm
        self.engine = ConstraintEngine()

    async def run(self, input: ConstraintAgentInput) -> AgentResult[ConstraintAgentOutput]:
        result = self.engine.check(
            total_cost=input.total_cost,
            budget=input.budget,
            hotels=input.hotels,
            max_hotel_price_per_night=input.max_hotel_price_per_night,
            budget_currency=input.budget_currency,
            travellers=input.travellers,
            expected_travellers=input.expected_travellers,
            duration_days=input.duration_days,
            expected_duration_days=input.expected_duration_days,
        )
        explanation = await explain_result(self.llm, result)

        return AgentResult(
            success=True,
            data=ConstraintAgentOutput(result=result, explanation=explanation),
        )