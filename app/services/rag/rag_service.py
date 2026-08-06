"""Top-level RAG orchestration: retrieve, gate on confidence, generate,
and hand back a structured, citable answer."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.rag.generation_provider import GenerationProvider
from app.services.rag.retriever import Retriever


@dataclass(frozen=True)
class RagSource:
    source: str
    title: str
    score: float
    excerpt: str


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    sources: list[RagSource]
    confidence: float
    grounded: bool


class RAGService:
    def __init__(
        self,
        retriever: Retriever,
        generation_provider: GenerationProvider,
        *,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> None:
        self._retriever = retriever
        self._generator = generation_provider
        self._top_k = top_k
        self._min_score = min_score

    def answer(self, query: str) -> RagAnswer:
        retrieved = self._retriever.retrieve(query, top_k=self._top_k)
        relevant = [r for r in retrieved if r.score >= self._min_score]

        if not relevant:
            return RagAnswer(
                answer=(
                    "I don't have grounded information in my knowledge base to "
                    "answer that confidently. Try rephrasing, or ask about a "
                    "specific section/topic (e.g. Section 80C, HRA, old vs new "
                    "regime)."
                ),
                sources=[],
                confidence=0.0,
                grounded=False,
            )

        answer_text = self._generator.generate(query, relevant)
        confidence = relevant[0].score

        return RagAnswer(
            answer=answer_text,
            sources=[
                RagSource(
                    source=r.passage.source,
                    title=r.passage.title,
                    score=r.score,
                    excerpt=r.passage.text[:280],
                )
                for r in relevant
            ],
            confidence=confidence,
            grounded=True,
        )
