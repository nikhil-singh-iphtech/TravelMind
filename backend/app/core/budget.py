# app/core/budget.py
from decimal import Decimal

from app.core.currency import convert
from app.schemas.results import BudgetResult
from app.schemas.travel import Activity, Flight, Hotel


class BudgetCalculator:
    def calculate(
        self,
        budget: Decimal,
        flights: list[Flight],
        hotels: list[Hotel],
        activities: list[Activity],
        transport: Decimal = Decimal("0"),
        food: Decimal = Decimal("0"),
        currency: str = "INR",
    ) -> BudgetResult:
        total = Decimal("0")
        total += sum((convert(f.price, f.currency, currency) for f in flights), Decimal("0"))
        total += sum((convert(h.total_price, h.currency, currency) for h in hotels), Decimal("0"))
        total += sum((convert(a.price, a.currency, currency) for a in activities), Decimal("0"))
        total += Decimal(transport) + Decimal(food)  # already in the budget currency

        return BudgetResult(total=total, budget=budget, passed=total <= budget)