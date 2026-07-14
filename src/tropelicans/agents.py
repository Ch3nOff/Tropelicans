"""Lazy agent registry and local model routing primitives."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AgentConfig
from .models import GenerationOptions, LocalModelRunner


@dataclass
class AgentResult:
    agent: str
    category: str
    model: str
    text: str


class Agent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.active = config.active_by_default
        self._runner: LocalModelRunner | None = None

    def activate(self) -> None:
        self.active = True

    def run(self, prompt: str, context: str = "") -> AgentResult:
        full_prompt = prompt if not context else f"{prompt}\n\nContext:\n{context}"
        if self.config.backend == "echo":
            text = f"[{self.config.category}:{self.config.model}] {full_prompt}"
        else:
            text = self._local_runner().generate(full_prompt)
        return AgentResult(self.config.name, self.config.category, self.config.model, text)

    def _local_runner(self) -> LocalModelRunner:
        if self._runner is None:
            self._runner = LocalModelRunner(
                self.config.model,
                task=self.config.task,
                options=GenerationOptions(
                    max_new_tokens=self.config.max_new_tokens,
                    temperature=self.config.temperature,
                ),
            )
        return self._runner


class AgentRouter:
    def __init__(self, agents: dict[str, AgentConfig], default_agent: str, lazy_activation: bool = True) -> None:
        self.default_agent = default_agent
        self.lazy_activation = lazy_activation
        self.agents = {name: Agent(config) for name, config in agents.items()}
        if default_agent in self.agents:
            self.agents[default_agent].activate()

    def route(self, prompt: str, category: str | None = None, context: str = "") -> AgentResult:
        agent = self._select_agent(category)
        if self.lazy_activation and not agent.active:
            agent.activate()
        return agent.run(prompt, context)

    def active_agents(self) -> list[str]:
        return [name for name, agent in self.agents.items() if agent.active]

    def _select_agent(self, category: str | None) -> Agent:
        if category:
            for agent in self.agents.values():
                if agent.config.category == category or agent.config.name == category:
                    return agent
        return self.agents[self.default_agent]
