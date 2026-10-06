from app.schemas.tools import HotelSearchInput
from app.schemas.travel import Hotel
from app.services.hotel_service import HotelService

_service = HotelService()


async def search_hotels(input: HotelSearchInput) -> list[Hotel]:
    """
    This is the function an LLM's tool call will eventually invoke.
    It takes validated input, delegates to the service layer, and
    returns validated output — the LLM never touches HotelService
    or the provider directly.
    """
    return await _service.search_hotels(input)