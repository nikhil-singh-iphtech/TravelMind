import logging
from app.schemas.destination import DestinationResource

logger = logging.getLogger(__name__)

MOCK_DESTINATION_LINKS = {
    "tokyo": [
        DestinationResource(
            title="Best Time to Visit Tokyo: Weather & Seasonal Guide",
            url="https://www.japan-guide.com/e/e2164.html",
            source_site="Japan Guide",
            snippet="Spring (cherry blossom season in April) and autumn (October to November) offer mild weather and spectacular foliage."
        ),
        DestinationResource(
            title="Top Places to Visit in Tokyo",
            url="https://www.gotokyo.org/en/destinations/index.html",
            source_site="Go Tokyo Official",
            snippet="Explore Senso-ji Temple in Asakusa, Shibuya Crossing, Meiji Shrine, and the traditional streets of Yanaka."
        ),
        DestinationResource(
            title="Tokyo Travel Guide & Itineraries",
            url="https://www.lonelyplanet.com/japan/tokyo",
            source_site="Lonely Planet",
            snippet="Discover Tokyo's neon-lit skyscrapers, world-class culinary scene, quiet gardens, and historic shrines."
        )
    ],
    "kyoto": [
        DestinationResource(
            title="Best Time to Visit Kyoto",
            url="https://www.japan-guide.com/e/e2158.html",
            source_site="Japan Guide",
            snippet="November and April are prime months to experience colorful maple leaves and cherry blossoms across Kyoto's temples."
        ),
        DestinationResource(
            title="Top 10 Attractions in Kyoto",
            url="https://kyoto.travel/en/see-and-do/index.html",
            source_site="Kyoto Official Travel Guide",
            snippet="Visit Fushimi Inari Taisha shrine, Kinkaku-ji (Golden Pavilion), Arashiyama Bamboo Grove, and Gion district."
        )
    ]
}

DEFAULT_LINKS = [
    DestinationResource(
        title="Official Travel & Destination Guide",
        url="https://www.wikivoyage.org/",
        source_site="WikiVoyage",
        snippet="Free, crowdsourced world travel guide with reliable safety, transport, and sightseeing tips."
    ),
    DestinationResource(
        title="Lonely Planet Destination Highlights",
        url="https://www.lonelyplanet.com/",
        source_site="Lonely Planet",
        snippet="Expert travel guides, itineraries, food recommendations, and cultural highlights."
    )
]


class MockSearchProvider:
    """Mock search provider returning safe, sanitized destination travel links."""

    async def search(self, query: str, destination: str) -> list[DestinationResource]:
        key = destination.lower().strip()
        results = MOCK_DESTINATION_LINKS.get(key, DEFAULT_LINKS)
        return results
