import httpx

from app.schemas.tools import WeatherInput
from app.schemas.weather import WeatherInfo

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes, simplified — https://open-meteo.com/en/docs
WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


class OpenMeteoError(Exception):
    """Raised when Open-Meteo can't be reached, or returns something unusable."""


class RealWeatherProvider:
    """
    No API key needed. Two real calls under the hood: geocode the
    city name to coordinates, then fetch the forecast for that
    location. The agent above never sees either HTTP call — same
    promise the Agent/Tool/Service/Provider split made back in Phase 4.
    """

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    async def get(self, input: WeatherInput) -> WeatherInfo:
        latitude, longitude = await self._geocode(input.city)
        return await self._forecast(input, latitude, longitude)

    async def _geocode(self, city: str) -> tuple[float, float]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(GEOCODING_URL, params={"name": city, "count": 1})
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise OpenMeteoError(f"geocoding request failed for '{city}': {exc}") from exc

        results = response.json().get("results")
        if not results:
            raise OpenMeteoError(f"no location found for '{city}'")

        top = results[0]
        return top["latitude"], top["longitude"]

    async def _forecast(self, input: WeatherInput, latitude: float, longitude: float) -> WeatherInfo:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,weathercode",
            "timezone": "auto",
            "start_date": input.target_date.isoformat(),
            "end_date": input.target_date.isoformat(),
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(FORECAST_URL, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise OpenMeteoError(f"forecast request failed: {exc}") from exc

        daily = response.json().get("daily")
        if not daily or not daily.get("time"):
            raise OpenMeteoError(
                f"no forecast data for {input.city} on {input.target_date} "
                f"(Open-Meteo's free tier only covers roughly the next 16 days)"
            )

        temperature = daily["temperature_2m_max"][0]
        code = daily["weathercode"][0]
        condition = WEATHER_CODE_DESCRIPTIONS.get(code, f"Unknown (code {code})")

        return WeatherInfo(
            city=input.city, target_date=input.target_date,
            temperature_celsius=temperature, condition=condition,
        )