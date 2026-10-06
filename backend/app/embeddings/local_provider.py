from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.embeddings.base import EmbeddingProvider


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Local embeddings — no API key, no network call per request. The
    model downloads once (around 90 MB) the first time it's used, then
    runs on CPU. Loading it is slow (a second or two); do it once per
    process, not per request.
    """

    def __init__(self, model_name: str | None = None):
        self._model = SentenceTransformer(model_name or settings.embedding_model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]