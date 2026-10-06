from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo


class MockWeatherProvider:
    async def get(self, input: WeatherInput) -> WeatherInfo:
        return WeatherInfo(
            city=input.city,
            target_date=input.target_date,
            temperature_celsius=22.0,
            condition="Clear",
        )