from datetime import date
from decimal import Decimal

import pytest

from app.schemas.tools import (
    HotelSearchInput,
    FlightSearchInput,
    ActivitySearchInput,
    WeatherInput,
)
from app.tools.registry import TOOLS


@pytest.mark.asyncio
async def test_search_hotels_filters_by_max_price():
    input = HotelSearchInput(
        city="Tokyo",
        check_in=date(2026, 11, 1),
        check_out=date(2026, 11, 8),
        guests=2,
        max_price_per_night=Decimal("10000"),
    )

    result = await TOOLS["search_hotels"](input)

    assert all(h.price_per_night <= Decimal("10000") for h in result)
    assert all(h.nights == 7 for h in result)


@pytest.mark.asyncio
async def test_search_flights_scales_with_travellers():
    input = FlightSearchInput(
        origin="Delhi",
        destination="Tokyo",
        departure_date=date(2026, 11, 1),
        travellers=2,
    )

    result = await TOOLS["search_flights"](input)

    assert len(result) == 2
    assert all(f.price == Decimal("64000") or f.price == Decimal("80000") for f in result)


@pytest.mark.asyncio
async def test_search_activities_respects_max_price():
    input = ActivitySearchInput(city="Tokyo", max_price=Decimal("2000"))

    result = await TOOLS["search_activities"](input)

    assert all(a.price <= Decimal("2000") for a in result)


@pytest.mark.asyncio
async def test_get_weather_returns_info_for_requested_city():
    input = WeatherInput(city="Tokyo", target_date=date(2026, 11, 1))

    result = await TOOLS["get_weather"](input)

    assert result.city == "Tokyo"
    assert result.target_date == date(2026, 11, 1)


def test_hotel_search_input_rejects_bad_dates():
    with pytest.raises(ValueError):
        HotelSearchInput(
            city="Tokyo",
            check_in=date(2026, 11, 8),
            check_out=date(2026, 11, 1),  # before check_in — invalid
            guests=2,
            max_price_per_night=Decimal("10000"),
        )