"""Loads the knowledge base corpus, embeds it, and answers similarity
queries against it. This is the retrieval half of Retrieval-Augmented
Generation — the piece that did not exist anywhere in the legacy codebase
despite the project being named around it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.services.rag.embedding_provider import EmbeddingProvider
from app.services.rag.vector_store import VectorStore


@dataclass(frozen=True)
class Passage:
    text: str
    source: str
    title: str


@dataclass(frozen=True)
class RetrievedPassage:
    passage: Passage
    score: float


def load_knowledge_base(directory: Path) -> list[Passage]:
    """Loads every .md file in `directory` and splits it into
    paragraph-level passages, tagged with the source filename and the
    document's title (first heading)."""
    passages: list[Passage] = []
    for md_file in sorted(directory.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else md_file.stem

        body = "\n".join(lines[1:]) if lines and lines[0].startswith("#") else content
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

        for paragraph in paragraphs:
            passages.append(Passage(text=paragraph, source=md_file.name, title=title))

    return passages


class Retriever:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        passages: list[Passage],
    ) -> None:
        if not passages:
            raise ValueError("Cannot build a retriever over an empty knowledge base.")

        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._passages = passages

        # Prepend the title when embedding (but not when displaying) so a
        # document's subject anchors its passages more strongly than
        # incidental keyword overlap with other documents.
        matrix = self._embedding_provider.fit_transform(
            [f"{p.title}. {p.text}" for p in passages]
        )
        self._vector_store.index(matrix)

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> "Retriever":
        return cls(embedding_provider, vector_store, load_knowledge_base(directory))

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedPassage]:
        query_vector = self._embedding_provider.transform(query)
        results = self._vector_store.search(query_vector, top_k=top_k)
        return [
            RetrievedPassage(passage=self._passages[r.index], score=r.score) for r in results
        ]
