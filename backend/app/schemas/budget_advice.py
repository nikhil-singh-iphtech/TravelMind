from decimal import Decimal
from typing import Literal
from pydantic import BaseModel


class BudgetSuggestion(BaseModel):
    component: Literal["flight", "hotel", "activities", "food", "transport", "duration"]
    action: str
    estimated_saving: Decimal
    resulting_total: Decimal


class BudgetAdvice(BaseModel):
    status: Literal["within_budget", "reducible", "increase_needed"]
    gap: Decimal
    cheapest_possible_total: Decimal
    recommended_budget: Decimal
    suggestions: list[BudgetSuggestion] = []
