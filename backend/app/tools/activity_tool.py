from app.schemas.tools import ActivitySearchInput
from app.schemas.travel import Activity
from app.services.activity_service import ActivityService

_service = ActivityService()


async def search_activities(input: ActivitySearchInput) -> list[Activity]:
    return await _service.search_activities(input)