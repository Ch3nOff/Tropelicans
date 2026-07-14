"""Configuration loading for Tropelicans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import RECOMMENDED_MODELS, RECOMMENDED_TASKS


@dataclass(frozen=True)
class AgentConfig:
    name: str
    category: str
    model: str
    active_by_default: bool = False
    backend: str = "huggingface"
    task: str = "text-generation"
    max_new_tokens: int = 256
    temperature: float = 0.7


@dataclass(frozen=True)
class MemoryConfig:
    working_memory: bool = True
    session_memory: bool = True
    project_memory: bool = True
    user_memory: bool = True
    incident_memory: bool = True
    importance_threshold: float = 0.7


@dataclass(frozen=True)
class WorkspaceConfig:
    track_user_changes: bool = True
    track_ai_changes: bool = True


@dataclass(frozen=True)
class WebViewConfig:
    onboarding: bool = True
    customizable: bool = True
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass(frozen=True)
class TropelicansConfig:
    default_agent: str = "text"
    lazy_agent_activation: bool = True
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    web_view: WebViewConfig = field(default_factory=WebViewConfig)


def default_config() -> TropelicansConfig:
    return TropelicansConfig(
        agents={
            "text": AgentConfig("text", "general", RECOMMENDED_MODELS["general"], True),
            "reasoning": AgentConfig("reasoning", "reasoning", RECOMMENDED_MODELS["reasoning"], False),
            "coding": AgentConfig("coding", "coding", RECOMMENDED_MODELS["coding"], False),
            "vision": AgentConfig("vision", "vision", RECOMMENDED_MODELS["vision"], False, task=RECOMMENDED_TASKS["vision"]),
        }
    )


def load_config(path: Path | None = None) -> TropelicansConfig:
    if path is None or not path.exists():
        return default_config()

    raw = json.loads(path.read_text(encoding="utf-8"))
    base = default_config()
    runtime = raw.get("runtime", {})
    agents = {
        name: AgentConfig(
            name=name,
            category=value.get("category", name),
            model=value.get("model", RECOMMENDED_MODELS.get(value.get("category", name), RECOMMENDED_MODELS["general"])),
            active_by_default=value.get("activeByDefault", False),
            backend=value.get("backend", "huggingface"),
            task=value.get("task", RECOMMENDED_TASKS.get(value.get("category", name), "text-generation")),
            max_new_tokens=value.get("maxNewTokens", 256),
            temperature=value.get("temperature", 0.7),
        )
        for name, value in raw.get("agents", {}).items()
    } or base.agents
    memory = raw.get("memory", {})
    workspace = raw.get("workspace", {})
    web_view = raw.get("webView", {})
    return TropelicansConfig(
        default_agent=runtime.get("defaultAgent", base.default_agent),
        lazy_agent_activation=runtime.get("lazyAgentActivation", base.lazy_agent_activation),
        agents=agents,
        memory=MemoryConfig(
            working_memory=memory.get("workingMemory", True),
            session_memory=memory.get("sessionMemory", True),
            project_memory=memory.get("projectMemory", True),
            user_memory=memory.get("userMemory", True),
            incident_memory=memory.get("incidentMemory", True),
            importance_threshold=memory.get("importanceThreshold", 0.7),
        ),
        workspace=WorkspaceConfig(
            track_user_changes=workspace.get("trackUserChanges", True),
            track_ai_changes=workspace.get("trackAiChanges", True),
        ),
        web_view=WebViewConfig(
            onboarding=web_view.get("onboarding", True),
            customizable=web_view.get("customizable", True),
            host=web_view.get("host", "127.0.0.1"),
            port=web_view.get("port", 8765),
        ),
    )


def config_to_dict(config: TropelicansConfig) -> dict[str, Any]:
    return {
        "runtime": {"defaultAgent": config.default_agent, "lazyAgentActivation": config.lazy_agent_activation},
        "agents": {
            name: {
                "category": agent.category,
                "model": agent.model,
                "activeByDefault": agent.active_by_default,
                "backend": agent.backend,
                "task": agent.task,
                "maxNewTokens": agent.max_new_tokens,
                "temperature": agent.temperature,
            }
            for name, agent in config.agents.items()
        },
        "memory": {
            "workingMemory": config.memory.working_memory,
            "sessionMemory": config.memory.session_memory,
            "projectMemory": config.memory.project_memory,
            "userMemory": config.memory.user_memory,
            "incidentMemory": config.memory.incident_memory,
            "importanceThreshold": config.memory.importance_threshold,
        },
        "workspace": {
            "trackUserChanges": config.workspace.track_user_changes,
            "trackAiChanges": config.workspace.track_ai_changes,
        },
        "webView": {
            "onboarding": config.web_view.onboarding,
            "customizable": config.web_view.customizable,
            "host": config.web_view.host,
            "port": config.web_view.port,
        },
    }
