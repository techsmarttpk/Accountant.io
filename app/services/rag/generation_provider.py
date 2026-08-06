"""Answer generation, grounded strictly in retrieved passages.

This replaces the legacy approach of calling raw GPT-2 `generate()` with
no retrieval step at all. Two problems with that approach: (1) GPT-2-small
has no reliable factual grounding for tax law regardless of fine-tuning,
and (2) nothing prevented it from confidently generating a wrong number or
rule. The default provider here is deliberately extractive — it never
invents text, it only returns and lightly stitches together the passages
the retriever actually found, each with a citation back to its source
file. This trades fluency for trustworthiness, which is the correct
trade-off for a fintech assistant.

`LLMGenerationProvider` is the seam for plugging in a real instruction-
tuned model (OpenAI/Anthropic/local) once an API key is available — it
should still be called with the retrieved passages as context and
instructed to answer only from them, preserving the grounding guarantee.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.rag.retriever import RetrievedPassage


class GenerationProvider(ABC):
    @abstractmethod
    def generate(self, query: str, passages: list[RetrievedPassage]) -> str: ...


class ExtractiveGenerationProvider(GenerationProvider):
    def generate(self, query: str, passages: list[RetrievedPassage]) -> str:
        if not passages:
            return "I don't have grounded information to answer that."

        parts = []
        for rp in passages:
            parts.append(f"From {rp.passage.title} ({rp.passage.source}):\n{rp.passage.text}")
        return "\n\n".join(parts)


class LLMGenerationProvider(GenerationProvider):
    """Not implemented — no LLM API key is configured in this environment.

    Intentionally raises rather than silently falling back, so a
    misconfiguration is visible immediately rather than degrading answer
    quality without anyone noticing.
    """

    def __init__(self, api_key: str | None = None, model: str = "") -> None:
        self._api_key = api_key
        self._model = model

    def generate(self, query: str, passages: list[RetrievedPassage]) -> str:
        raise NotImplementedError(
            "LLMGenerationProvider requires a configured API key and provider "
            "integration — wire it up here when moving beyond extractive answers."
        )
