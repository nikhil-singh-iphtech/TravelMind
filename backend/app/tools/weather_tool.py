from app.core.config import settings
from app.providers.mock_weather import MockWeatherProvider
from app.providers.real_weather import RealWeatherProvider
from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo
from app.services.weather_service import WeatherService

# The only line that changes in this whole phase: which provider
# WeatherService wraps. Everything else — the agent, the service,
# the tool's own function signature below — is untouched.
_provider = RealWeatherProvider() if settings.use_real_weather else MockWeatherProvider()
_service = WeatherService(_provider)


async def get_weather(input: WeatherInput) -> WeatherInfo:
    return await _service.get_weather(input)