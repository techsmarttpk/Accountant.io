"""In-memory vector store.

Holds the embedded knowledge-base matrix and does cosine-similarity
search against it. Fine for a knowledge base of dozens to low thousands
of passages, rebuilt on process start. The interface is the seam for
swapping in pgvector or a dedicated vector DB (FAISS, Qdrant) once the
corpus outgrows "fits comfortably in memory" — nothing above this layer
(the retriever) needs to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class VectorSearchResult:
    index: int
    score: float


class VectorStore(ABC):
    @abstractmethod
    def index(self, matrix: Any) -> None: ...

    @abstractmethod
    def search(self, query_vector: Any, top_k: int) -> list[VectorSearchResult]: ...


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._matrix = None

    def index(self, matrix: Any) -> None:
        self._matrix = matrix

    def search(self, query_vector: Any, top_k: int) -> list[VectorSearchResult]:
        if self._matrix is None:
            raise RuntimeError("VectorStore.index() must be called before search().")

        scores = cosine_similarity(query_vector, self._matrix)[0]
        ranked_indices = scores.argsort()[::-1][:top_k]
        return [VectorSearchResult(index=int(i), score=float(scores[i])) for i in ranked_indices]
