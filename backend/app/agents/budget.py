from decimal import Decimal

from pydantic import BaseModel

from app.agents.base import AgentResult, explain_result
from app.core.budget import BudgetCalculator
from app.llm.base import LLMProvider
from app.schemas import Activity, BudgetResult, Flight, Hotel


class BudgetAgentInput(BaseModel):
    budget: Decimal
    flights: list[Flight]
    hotels: list[Hotel]
    activities: list[Activity]
    transport: Decimal = Decimal("0")
    food: Decimal = Decimal("0")


class BudgetAgentOutput(BaseModel):
    result: BudgetResult
    explanation: str


class BudgetAgent:
    """
    Python computes the verdict. The LLM (optional) only explains it.
    """

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm
        self.calculator = BudgetCalculator()

    async def run(self, input: BudgetAgentInput) -> AgentResult[BudgetAgentOutput]:
        result = self.calculator.calculate(
            budget=input.budget,
            flights=input.flights,
            hotels=input.hotels,
            activities=input.activities,
            transport=input.transport,
            food=input.food,
        )
        explanation = await explain_result(self.llm, result)

        return AgentResult(
            success=True,
            data=BudgetAgentOutput(result=result, explanation=explanation),
        )