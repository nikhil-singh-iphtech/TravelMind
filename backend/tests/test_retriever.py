import pytest

from app.db.models.document_chunk import DocumentChunk
from app.db.session import SessionLocal
from app.schemas.rag import GuideChunk
from app.services.retriever_service import RetrieverService
from tests.fakes import FakeEmbeddingProvider


@pytest.fixture
def retriever():
    return RetrieverService(FakeEmbeddingProvider())


@pytest.fixture(autouse=True)
def cleanup_test_chunks():
    yield
    with SessionLocal() as session:
        session.query(DocumentChunk).filter(DocumentChunk.source.like("test_%")).delete()
        session.commit()


async def test_ingest_and_retrieve_returns_matching_chunk(retriever):
    chunks = [
        GuideChunk(source="test_tokyo.md", city="Tokyo", content="Tokyo temples and shrines in Asakusa."),
        GuideChunk(source="test_paris.md", city="Paris", content="Paris museums along the Seine."),
    ]
    await retriever.ingest(chunks)

    results = await retriever.retrieve(query="Tokyo temples and shrines in Asakusa.", top_k=1)

    assert len(results) == 1
    assert results[0].source == "test_tokyo.md"


async def test_retrieve_filters_by_city(retriever):
    chunks = [
        GuideChunk(source="test_tokyo2.md", city="Tokyo", content="Outdoor parks and rivers in Tokyo."),
        GuideChunk(source="test_kyoto2.md", city="Kyoto", content="Outdoor parks and rivers in Kyoto."),
    ]
    await retriever.ingest(chunks)

    results = await retriever.retrieve(query="outdoor parks and rivers", city="Kyoto", top_k=5)

    kyoto_test_results = [r for r in results if r.source == "test_kyoto2.md"]
    assert len(kyoto_test_results) == 1