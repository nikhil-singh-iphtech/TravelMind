from decimal import Decimal

from app.core.constraints import ConstraintEngine
from app.schemas import Hotel


def test_constraints_pass_when_all_satisfied():
    engine = ConstraintEngine()

    result = engine.check(
        total_cost=Decimal("180000"),
        budget=Decimal("200000"),
        hotels=[Hotel(id="h1", name="Hotel A", city="Tokyo",
                       price_per_night=Decimal("8000"), nights=10)],
        max_hotel_price_per_night=Decimal("10000"),
        travellers=2,
        expected_travellers=2,
        duration_days=7,
        expected_duration_days=7,
    )

    assert result.passed is True
    assert result.violations == []


def test_constraints_report_multiple_violations():
    engine = ConstraintEngine()

    result = engine.check(
        total_cost=Decimal("235000"),
        budget=Decimal("200000"),
        hotels=[Hotel(id="h1", name="Hotel A", city="Tokyo",
                       price_per_night=Decimal("15000"), nights=10)],
        max_hotel_price_per_night=Decimal("10000"),
        travellers=3,
        expected_travellers=2,
        duration_days=7,
        expected_duration_days=7,
    )

    assert result.passed is False
    violation_names = {v.constraint for v in result.violations}
    assert "budget" in violation_names
    assert "hotel_price:h1" in violation_names
    assert "travellers" in violation_names