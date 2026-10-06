from app.providers.mock_weather import MockWeatherProvider
from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo


class WeatherService:
    def __init__(self, provider: MockWeatherProvider | None = None):
        self.provider = provider or MockWeatherProvider()

    async def get_weather(self, input: WeatherInput) -> WeatherInfo:
        return await self.provider.get(input)