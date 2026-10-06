from app.providers.mock_activity import MockActivityProvider
from app.schemas.tools import ActivitySearchInput
from app.schemas.travel import Activity


class ActivityService:
    def __init__(self, provider: MockActivityProvider | None = None):
        self.provider = provider or MockActivityProvider()

    async def search_activities(self, input: ActivitySearchInput) -> list[Activity]:
        return await self.provider.search(input)