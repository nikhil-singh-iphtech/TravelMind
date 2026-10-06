from decimal import Decimal

from app.schemas import Flight, Hotel, Activity, BudgetResult


class BudgetCalculator:
    """
    Deterministic budget math. No LLM involved — this class exists
    specifically so nothing else in the system has to trust a model
    to add numbers correctly.
    """

    def calculate(
        self,
        budget: Decimal,
        flights: list[Flight],
        hotels: list[Hotel],
        activities: list[Activity],
        transport: Decimal = Decimal("0"),
        food: Decimal = Decimal("0"),
    ) -> BudgetResult:
        flights_total = sum((f.price for f in flights), Decimal("0"))
        hotels_total = sum((h.total_price for h in hotels), Decimal("0"))
        activities_total = sum((a.price for a in activities), Decimal("0"))

        total = flights_total + hotels_total + activities_total + transport + food

        return BudgetResult(
            total=total,
            budget=budget,
            passed=total <= budget,
        )