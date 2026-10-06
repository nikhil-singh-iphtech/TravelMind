from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Turns text into vectors. Same shape as LLMProvider — one interface,
    swappable implementations (local today, an API later if needed).
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError