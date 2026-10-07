from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.config import settings
from app.providers.real_flight import RealFlightProvider

pytestmark = pytest.mark.skipif(
    not settings.duffel_api_key, reason="DUFFEL_API_KEY not set — skipping live Duffel tests"
)


async def test_real_flight_provider_returns_flights():
    from app.schemas.tools import FlightSearchInput

    provider = RealFlightProvider()
    departure = date.today() + timedelta(days=30)

    result = await provider.search(FlightSearchInput(
        origin="London", destination="New York", departure_date=departure, travellers=1, currency="GBP",
    ))

    assert len(result) > 0
    assert all(isinstance(f.price, Decimal) for f in result)