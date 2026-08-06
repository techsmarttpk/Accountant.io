"""Embedding provider abstraction.

Default implementation is TF-IDF (via scikit-learn) rather than a dense
neural embedding model. This is a deliberate engineering trade-off, not a
missing feature: TF-IDF requires no GPU, no multi-hundred-MB model
download, is fully deterministic, and is genuinely strong for this
use-case — retrieval over a small, curated, keyword-dense corpus of tax
FAQ content, where matching on terms like "80C" or "HRA" matters more
than semantic paraphrase understanding.

`EmbeddingProvider` is the seam for upgrading to dense embeddings (e.g.
sentence-transformers, or an embeddings API) once the knowledge base grows
large enough that lexical matching stops being sufficient — swap the
implementation bound in `app.api.deps`, nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer


class EmbeddingProvider(ABC):
    @abstractmethod
    def fit_transform(self, documents: list[str]) -> Any: ...

    @abstractmethod
    def transform(self, text: str) -> Any: ...


class TfidfEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._fitted = False

    def fit_transform(self, documents: list[str]):
        matrix = self._vectorizer.fit_transform(documents)
        self._fitted = True
        return matrix

    def transform(self, text: str):
        if not self._fitted:
            raise RuntimeError("EmbeddingProvider.fit_transform must be called before transform().")
        return self._vectorizer.transform([text])
