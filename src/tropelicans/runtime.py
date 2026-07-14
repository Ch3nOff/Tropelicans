"""High-level Tropelicans runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agents import AgentResult, AgentRouter
from .config import TropelicansConfig, load_config
from .memory import MemoryManager
from .skills import SkillRegistry
from .workspace import WorkspaceChange, WorkspaceManager


@dataclass
class RuntimeResult:
    response: AgentResult
    active_agents: list[str]
    workspace_changes: list[WorkspaceChange]
    matched_skills: list[str]


class TropelicansRuntime:
    def __init__(self, workspace: Path, config_path: Path | None = None) -> None:
        self.workspace = workspace.resolve()
        self.config: TropelicansConfig = load_config(config_path)
        self.router = AgentRouter(self.config.agents, self.config.default_agent, self.config.lazy_agent_activation)
        self.workspace_manager = WorkspaceManager(self.workspace)
        tropelicans_dir = self.workspace / ".tropelicans"
        self.memory = MemoryManager(tropelicans_dir / "memory", self.config.memory.importance_threshold)
        self.skills = SkillRegistry(tropelicans_dir / "skills")

    def run(self, prompt: str, category: str | None = None) -> RuntimeResult:
        workspace_changes = self.workspace_manager.changes()
        matched_skills = self.skills.match(prompt)
        context_parts = []
        if workspace_changes:
            context_parts.append("Workspace changes: " + ", ".join(f"{item.status}:{item.path}" for item in workspace_changes))
        if matched_skills:
            context_parts.append("Skills: " + ", ".join(skill.name for skill in matched_skills))
        response = self.router.route(prompt, category=category, context="\n".join(context_parts))
        self.memory.remember("session", prompt, importance=0.3, tags=["prompt"])
        if workspace_changes:
            self.memory.remember("project", context_parts[0], importance=self.config.memory.importance_threshold, tags=["workspace-change"])
        return RuntimeResult(response, self.router.active_agents(), workspace_changes, [skill.name for skill in matched_skills])
