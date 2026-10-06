from decimal import Decimal

from app.schemas.tools import ActivitySearchInput
from app.schemas.travel import Activity


class MockActivityProvider:
    async def search(self, input: ActivitySearchInput) -> list[Activity]:
        candidates = [
            Activity(id="a1", name=f"{input.city} Cultural Walking Tour", price=Decimal("2500")),
            Activity(id="a2", name=f"{input.city} Food Experience", price=Decimal("3500")),
            Activity(id="a3", name=f"{input.city} Outdoor Hike", price=Decimal("1800")),
        ]

        if input.max_price is not None:
            candidates = [a for a in candidates if a.price <= input.max_price]

        return candidates