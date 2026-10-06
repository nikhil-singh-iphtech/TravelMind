from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight
from app.services.flight_service import FlightService

_service = FlightService()


async def search_flights(input: FlightSearchInput) -> list[Flight]:
    return await _service.search_flights(input)