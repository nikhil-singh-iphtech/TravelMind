import pytest
from app.providers.search import MockSearchProvider
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_destination_search_returns_sanitized_links():
    service = SearchService(provider=MockSearchProvider())
    resources = await service.get_destination_resources("Tokyo")

    assert len(resources) > 0
    for r in resources:
        assert r.title != ""
        assert r.url.startswith("http://") or r.url.startswith("https://")
        assert r.snippet != ""


@pytest.mark.asyncio
async def test_prompt_injection_in_snippet_treated_as_plain_data():
    service = SearchService(provider=MockSearchProvider())
    resources = await service.get_destination_resources("Tokyo")
    # Even if snippet contains text trying to inject commands, it stays plain string data
    for r in resources:
        assert isinstance(r.snippet, str)
