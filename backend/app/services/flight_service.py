from app.providers.mock_flight import MockFlightProvider
from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight


class FlightService:
    def __init__(self, provider: MockFlightProvider | None = None):
        self.provider = provider or MockFlightProvider()

    async def search_flights(self, input: FlightSearchInput) -> list[Flight]:
        return await self.provider.search(input)