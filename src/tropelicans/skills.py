"""User and AI generated skills."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    trigger: str
    instructions: str


class SkillRegistry:
    def __init__(self, skills_path: Path) -> None:
        self.skills_path = skills_path
        self.skills_path.mkdir(parents=True, exist_ok=True)

    def create(self, skill: Skill) -> Path:
        path = self.skills_path / f"{skill.name}.json"
        path.write_text(json.dumps(asdict(skill), indent=2), encoding="utf-8")
        return path

    def list(self) -> list[Skill]:
        skills: list[Skill] = []
        for path in sorted(self.skills_path.glob("*.json")):
            skills.append(Skill(**json.loads(path.read_text(encoding="utf-8"))))
        return skills

    def match(self, prompt: str) -> list[Skill]:
        text = prompt.lower()
        return [skill for skill in self.list() if skill.trigger.lower() in text]
