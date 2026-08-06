"""Local filesystem storage for uploaded documents/audio.

Fixes the single biggest concurrency bug in the legacy script: every
upload there was written to the same fixed filename (`user_input.pdf`),
so concurrent users silently overwrote each other's files. Every file
here gets a UUID-qualified path, namespaced by user.

This is swappable: production deployments handling real financial
documents should point this at an object store (S3-compatible) with
server-side encryption rather than local disk — that's a follow-up, not
a blocker, and the interface below is the seam to do it through.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    @abstractmethod
    def save(self, *, user_id: uuid.UUID, filename: str, content: bytes) -> str:
        """Persists `content` and returns a storage path/key."""

    @abstractmethod
    def read(self, storage_path: str) -> bytes: ...


class LocalFileStorage(FileStorage):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, *, user_id: uuid.UUID, filename: str, content: bytes) -> str:
        user_dir = self.root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
        path = user_dir / safe_name
        path.write_bytes(content)
        return str(path)

    def read(self, storage_path: str) -> bytes:
        return Path(storage_path).read_bytes()
