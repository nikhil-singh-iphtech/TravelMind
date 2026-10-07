from app.core.config import settings
from app.providers.mock_hotel import MockHotelProvider
from app.providers.real_hotel import RealHotelProvider
from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel
from app.services.hotel_service import HotelService

_provider = RealHotelProvider() if settings.use_real_hotels else MockHotelProvider()
_service = HotelService(_provider)


async def search_hotels(input: HotelSearchInput) -> list[Hotel]:
    return await _service.search_hotels(input)