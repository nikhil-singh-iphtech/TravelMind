from decimal import Decimal

from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel


class MockHotelProvider:
    """
    Stands in for a real hotel API. Returns a small, deterministic
    set of hotels so we can build/test the rest of the system
    without API keys or network calls.
    """

    async def search(self, input: HotelSearchInput) -> list[Hotel]:
        nights = (input.check_out - input.check_in).days

        candidates = [
            Hotel(
                id="h1",
                name=f"{input.city} Central Inn",
                city=input.city,
                price_per_night=Decimal("6000"),
                nights=nights,
                currency=input.currency,
            ),
            Hotel(
                id="h2",
                name=f"{input.city} Riverside Hotel",
                city=input.city,
                price_per_night=Decimal("9000"),
                nights=nights,
                currency=input.currency,
            ),
            Hotel(
                id="h3",
                name=f"{input.city} Luxury Suites",
                city=input.city,
                price_per_night=Decimal("18000"),
                nights=nights,
                currency=input.currency,
            ),
        ]

        return [h for h in candidates if h.price_per_night <= input.max_price_per_night]