from pathlib import Path

import pytest

from app.services.rag.embedding_provider import TfidfEmbeddingProvider
from app.services.rag.generation_provider import ExtractiveGenerationProvider
from app.services.rag.rag_service import RAGService
from app.services.rag.retriever import Retriever
from app.services.rag.vector_store import InMemoryVectorStore

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge_base"


@pytest.fixture
def rag_service() -> RAGService:
    retriever = Retriever.from_directory(
        KNOWLEDGE_BASE_DIR, TfidfEmbeddingProvider(), InMemoryVectorStore()
    )
    return RAGService(retriever, ExtractiveGenerationProvider(), top_k=3, min_score=0.05)


def test_retrieves_relevant_passage_for_80c_question(rag_service):
    answer = rag_service.answer("What deductions can I claim under Section 80C?")
    assert answer.grounded
    assert any(s.source == "section_80c.md" for s in answer.sources)


def test_retrieves_relevant_passage_for_hra_question(rag_service):
    answer = rag_service.answer("How is my HRA exemption calculated?")
    assert answer.grounded
    assert any(s.source == "hra_exemption.md" for s in answer.sources)


def test_out_of_domain_question_is_not_grounded(rag_service):
    answer = rag_service.answer("What is the best pizza topping?")
    assert not answer.grounded
    assert answer.sources == []
    assert answer.confidence == 0.0


def test_every_answer_carries_a_citable_source(rag_service):
    answer = rag_service.answer("Tell me about the health and education cess")
    if answer.grounded:
        for source in answer.sources:
            assert source.source.endswith(".md")
            assert source.excerpt
