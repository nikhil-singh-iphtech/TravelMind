from decimal import Decimal

from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight


class MockFlightProvider:
    async def search(self, input: FlightSearchInput) -> list[Flight]:
        base_price = Decimal("32000")
        return [
            Flight(
                id="f1",
                airline="IndiGo",
                price=base_price * input.travellers,
                currency=input.currency,
            ),
            Flight(
                id="f2",
                airline="Air India",
                price=(base_price + Decimal("8000")) * input.travellers,
                currency=input.currency,
            ),
        ]