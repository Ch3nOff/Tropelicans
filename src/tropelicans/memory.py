"""Memory stores for working, session, project, user, and incident knowledge."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass
class MemoryEntry:
    id: str
    scope: str
    content: str
    importance: float
    created_at: str
    tags: list[str]


class MemoryManager:
    def __init__(self, storage_path: Path, importance_threshold: float = 0.7) -> None:
        self.storage_path = storage_path
        self.importance_threshold = importance_threshold
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def remember(self, scope: str, content: str, importance: float = 0.5, tags: list[str] | None = None) -> MemoryEntry:
        entry = MemoryEntry(
            id=str(uuid4()),
            scope=scope,
            content=content,
            importance=importance,
            created_at=datetime.now(timezone.utc).isoformat(),
            tags=tags or [],
        )
        entries = self.list(scope)
        entries.append(entry)
        self._write(scope, entries)
        return entry

    def important(self, content: str, scope: str = "project", tags: list[str] | None = None) -> MemoryEntry:
        return self.remember(scope, content, self.importance_threshold, tags)

    def list(self, scope: str | None = None) -> list[MemoryEntry]:
        files = [self._file(scope)] if scope else sorted(self.storage_path.glob("*.json"))
        entries: list[MemoryEntry] = []
        for file in files:
            if not file.exists():
                continue
            payload = json.loads(file.read_text(encoding="utf-8"))
            entries.extend(MemoryEntry(**item) for item in payload)
        return entries

    def search(self, query: str) -> list[MemoryEntry]:
        needle = query.lower()
        return [entry for entry in self.list() if needle in entry.content.lower() or needle in " ".join(entry.tags).lower()]

    def _file(self, scope: str) -> Path:
        return self.storage_path / f"{scope}.json"

    def _write(self, scope: str, entries: list[MemoryEntry]) -> None:
        self._file(scope).write_text(json.dumps([asdict(entry) for entry in entries], indent=2), encoding="utf-8")
