from app.core.config import settings
from app.providers.mock_flight import MockFlightProvider
from app.providers.real_flight import RealFlightProvider
from app.schemas.tools import FlightSearchInput
from app.schemas.travel import Flight
from app.services.flight_service import FlightService

_provider = RealFlightProvider() if settings.use_real_flights else MockFlightProvider()
_service = FlightService(_provider)


async def search_flights(input: FlightSearchInput) -> list[Flight]:
    return await _service.search_flights(input)