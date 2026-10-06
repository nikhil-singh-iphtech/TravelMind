from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo
from app.services.weather_service import WeatherService

_service = WeatherService()


async def get_weather(input: WeatherInput) -> WeatherInfo:
    return await _service.get_weather(input)