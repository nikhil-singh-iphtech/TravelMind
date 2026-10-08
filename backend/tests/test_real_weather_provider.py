from datetime import date, timedelta

import pytest

from app.providers.real_weather import OpenMeteoError, RealWeatherProvider
from app.schemas.tools import WeatherInput


async def test_real_weather_provider_returns_data_for_a_near_term_date():
    """
    Uses a date 3 days out so this stays well within Open-Meteo's
    forecast window regardless of when this test actually runs.
    """
    provider = RealWeatherProvider()
    target = date.today() + timedelta(days=3)

    result = await provider.get(WeatherInput(city="Tokyo", target_date=target))

    assert result.city == "Tokyo"
    assert result.target_date == target
    assert isinstance(result.temperature_celsius, float)
    assert result.condition != ""


async def test_real_weather_provider_returns_fallback_for_unknown_city():
    provider = RealWeatherProvider()
    result = await provider.get(WeatherInput(city="Nowhereville Zzzqx", target_date=date.today()))
    assert result.condition == "Forecast not available yet"
    assert result.temperature_celsius is None