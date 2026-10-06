from decimal import Decimal

from app.core.budget import BudgetCalculator
from app.schemas import Flight, Hotel, Activity


def test_budget_passes_when_under_limit():
    calc = BudgetCalculator()

    result = calc.calculate(
        budget=Decimal("200000"),
        flights=[Flight(id="f1", airline="IndiGo", price=Decimal("65000"))],
        hotels=[Hotel(id="h1", name="Hotel A", city="Tokyo",
                       price_per_night=Decimal("9000"), nights=10)],
        activities=[Activity(id="a1", name="Temple Tour", price=Decimal("20000"))],
        transport=Decimal("10000"),
        food=Decimal("15000"),
    )

    assert result.total == Decimal("200000")
    assert result.passed is True


def test_budget_fails_when_over_limit():
    calc = BudgetCalculator()

    result = calc.calculate(
        budget=Decimal("200000"),
        flights=[Flight(id="f1", airline="IndiGo", price=Decimal("80000"))],
        hotels=[Hotel(id="h1", name="Hotel A", city="Tokyo",
                       price_per_night=Decimal("15000"), nights=10)],
        activities=[],
    )

    assert result.total == Decimal("230000")
    assert result.passed is False