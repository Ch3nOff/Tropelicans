"""Workspace inspection and change tracking."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspaceChange:
    path: str
    status: str


class WorkspaceManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._snapshot = self.snapshot()

    def snapshot(self) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for path in self.root.rglob("*"):
            if not path.is_file() or self._ignored(path):
                continue
            relative = path.relative_to(self.root).as_posix()
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes

    def changes(self) -> list[WorkspaceChange]:
        current = self.snapshot()
        changes: list[WorkspaceChange] = []
        for path in sorted(current.keys() - self._snapshot.keys()):
            changes.append(WorkspaceChange(path, "added"))
        for path in sorted(self._snapshot.keys() - current.keys()):
            changes.append(WorkspaceChange(path, "deleted"))
        for path in sorted(current.keys() & self._snapshot.keys()):
            if current[path] != self._snapshot[path]:
                changes.append(WorkspaceChange(path, "modified"))
        return changes

    def refresh(self) -> None:
        self._snapshot = self.snapshot()

    def _ignored(self, path: Path) -> bool:
        parts = set(path.relative_to(self.root).parts)
        return bool(parts & {".git", "__pycache__", ".pytest_cache", "node_modules"})
