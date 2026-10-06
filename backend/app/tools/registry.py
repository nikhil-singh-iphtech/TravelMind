from app.tools.hotel_tool import search_hotels
from app.tools.flight_tool import search_flights
from app.tools.activity_tool import search_activities
from app.tools.weather_tool import get_weather

# Name → callable. This is what an agent will look up a tool by
# name from once tool-calling is wired up in Phase 5/6. Deliberately
# just a dict — no plugin framework until we actually need one.
TOOLS = {
    "search_hotels": search_hotels,
    "search_flights": search_flights,
    "search_activities": search_activities,
    "get_weather": get_weather,
}