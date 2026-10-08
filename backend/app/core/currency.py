# app/core/currency.py
"""Simple currency conversion using a static rate table.

Rates are APPROXIMATE PLACEHOLDERS (INR per 1 unit). Update them before
trusting results. A live exchange-rate API can replace this later without
changing any caller.
"""
from decimal import Decimal

INR_PER_UNIT: dict[str, Decimal] = {
    "INR": Decimal("1"),
    "USD": Decimal("88"),
    "EUR": Decimal("102"),
    "GBP": Decimal("118"),
    "JPY": Decimal("0.58"),
}


class UnknownCurrencyError(ValueError):
    """Raised when we have no rate for a currency. We never guess."""


def convert(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    src = from_currency.upper()
    dst = to_currency.upper()
    if src == dst:
        return amount
    for code in (src, dst):
        if code not in INR_PER_UNIT:
            raise UnknownCurrencyError(f"No exchange rate for currency '{code}'")
    inr = amount * INR_PER_UNIT[src]
    return (inr / INR_PER_UNIT[dst]).quantize(Decimal("0.01"))