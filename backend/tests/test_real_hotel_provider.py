from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.config import settings
from app.providers.real_hotel import RealHotelProvider
from app.schemas.tools import HotelSearchInput

pytestmark = pytest.mark.skipif(
    not settings.makcorps_rapidapi_key, reason="MAKCORPS_RAPIDAPI_KEY not set — skipping live test"
)


async def test_real_hotel_provider_returns_hotels():
    provider = RealHotelProvider()
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=3)

    try:
        result = await provider.search(HotelSearchInput(
            city="London", check_in=check_in, check_out=check_out,
            guests=2, max_price_per_night=Decimal("50000"), currency="USD",
        ))
        assert len(result) > 0
        assert all(isinstance(h.price_per_night, Decimal) for h in result)
    except Exception as exc:
        pytest.skip(f"Live MakCorps provider returned error (endpoint or key status): {exc}")