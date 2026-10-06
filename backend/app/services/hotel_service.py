from app.providers.mock_hotel import MockHotelProvider
from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel


class HotelService:
    def __init__(self, provider: MockHotelProvider | None = None):
        # Later: pass a RealHotelProvider here instead — nothing
        # above this class needs to change.
        self.provider = provider or MockHotelProvider()

    async def search_hotels(self, input: HotelSearchInput) -> list[Hotel]:
        return await self.provider.search(input)