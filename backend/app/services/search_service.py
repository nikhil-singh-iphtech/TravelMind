import logging
from app.providers.search import MockSearchProvider
from app.schemas.destination import DestinationResource

logger = logging.getLogger(__name__)


class SearchService:
    """Service retrieving verified travel guide links for destinations."""

    def __init__(self, provider=None):
        self.provider = provider or MockSearchProvider()

    async def get_destination_resources(self, destination: str) -> list[DestinationResource]:
        try:
            query = f"best time to visit {destination} travel guide"
            resources = await self.provider.search(query, destination)
            return resources
        except Exception as exc:
            logger.error("Failed to fetch destination links for %s: %s", destination, exc)
            return []
