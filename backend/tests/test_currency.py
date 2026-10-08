# tests/test_currency.py
from decimal import Decimal

import pytest

from app.core.budget import BudgetCalculator
from app.core.currency import UnknownCurrencyError, convert
from app.schemas.travel import Flight, Hotel


def test_same_currency_is_unchanged():
    assert convert(Decimal("100"), "INR", "INR") == Decimal("100")


def test_eur_to_inr_uses_table():
    assert convert(Decimal("10"), "EUR", "INR") == Decimal("1020.00")


def test_unknown_currency_fails_loudly():
    with pytest.raises(UnknownCurrencyError):
        convert(Decimal("1"), "XYZ", "INR")


def test_budget_converts_mixed_currencies():
    flight = Flight(id="f", airline="X", price=Decimal("500"), currency="EUR")
    hotel = Hotel(id="h", name="H", city="Tokyo", price_per_night=Decimal("100"),
                  nights=2, currency="USD")
    result = BudgetCalculator().calculate(Decimal("60000"), [flight], [hotel], [])
    # 500 EUR = 51,000 INR ; 200 USD = 17,600 INR ; total 68,600 > 60,000
    assert result.total == Decimal("68600.00")
    assert result.passed is False