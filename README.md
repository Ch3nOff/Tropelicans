# Tropelicans

Tropelicans is an AI runtime framework for building customizable, workspace-aware AI systems. It is designed around a CLI-first workflow with a configurable web view so users can control how agents, memories, tools, and skills behave in their own environment.

## Vision

Tropelicans is not just a chat application. It is a framework where users can customize an AI runtime that combines specialized language models, persistent workspaces, memory, skills, and a visual second-brain knowledge layer.

The framework starts with a lightweight default runtime and activates only the capabilities needed for the current task. This keeps resource usage efficient while still allowing multiple specialized models to collaborate when the user enables them.

## Core ideas

### 1. Specialized LLM agents

Tropelicans treats LLMs as agents with different strengths. A user can assign models to categories such as:

- reasoning
- coding
- writing
- image and photo understanding
- planning
- research
- testing and debugging

Only the basic text agent is active by default. Additional agents stay inactive until the user enables them or a workflow needs them. When enabled, agents can communicate with each other in a mixture-of-experts style runtime, while still remaining separate models with separate abilities.

### 2. Workspace-aware AI

Tropelicans is intended to operate inside a user workspace, not only inside a chat thread. The AI can help build projects, inspect files, understand changes, and remember useful context about the workspace.

The runtime supports:

- project workspaces
- short-term task memory
- long-term user and project memory
- user-defined skills
- tool and command execution policies
- memory importance scoring
- automatic cleanup of one-time context

The goal is to help the AI decide what should be remembered permanently, what should stay temporary, and what should be discarded to control storage size and context quality.

### 3. Customizable CLI and web view

Tropelicans is CLI-first so users can run it locally and integrate it into their development workflow. The framework also provides a web view where users can configure the runtime visually.

The web view should support:

- onboarding for first-time users
- agent and model configuration
- memory inspection and editing
- workspace dashboards
- skill management
- runtime status and resource usage
- user-customizable interface settings

### 4. Second-brain knowledge layer

Tropelicans includes a knowledge view that acts like a second brain for the user and the AI. Over time, the system can learn preferences, project conventions, useful debugging notes, and repeated patterns.

Examples of knowledge the system can retain include:

- user preferences and writing style
- project architecture decisions
- recurring bugs and known fixes
- test failures and successful resolutions
- workspace changes made by the user
- important documents, notes, and references

When a similar issue happens again, the AI can use this stored knowledge to suggest better actions faster.

## Planned runtime layers

```text
CLI / Web View
      ↓
Runtime Orchestrator
      ↓
Agent Router ── Specialized LLM Agents
      ↓
Workspace Manager ── Tools ── Skills
      ↓
Memory Manager ── Knowledge Graph / Second Brain
```

## Current status

This repository currently contains the initial project definition and architecture direction. Implementation will be added incrementally.

## License

Tropelicans is licensed under the MIT License. See [LICENSE](LICENSE).

## Quick start

Tropelicans now includes a minimal Python framework implementation. Install the base framework for CLI, memory, workspace, skills, and web status features. Add the Hugging Face extra when you want local model execution and automatic model downloads.

```bash
pip install -e .
pip install -e ".[huggingface]"
```

```bash
python -m tropelicans.cli --workspace . init
python -m tropelicans.cli --workspace . status
python -m tropelicans.cli --workspace . models list
python -m tropelicans.cli --workspace . models download coding
python -m tropelicans.cli --workspace . run "Help me understand this project"
python -m tropelicans.cli --workspace . run "Write tests for this workspace" --category coding
python -m tropelicans.cli --workspace . web
```

After installation, the same commands are available through the `tropelicans` console script.

## Implemented modules

- `tropelicans.config` loads runtime, agent, memory, workspace, and web view settings.
- `tropelicans.agents` provides a lazy agent router with category-based dispatch.
- `tropelicans.workspace` snapshots the workspace and reports added, modified, or deleted files.
- `tropelicans.memory` stores working, session, project, user, and incident-style JSON memories.
- `tropelicans.skills` stores reusable user or AI-created skills.
- `tropelicans.runtime` coordinates agents, workspace changes, skills, and memory.
0- `tropelicans.web` serves a small local web view and JSON status endpoint.

## Local Hugging Face models

Tropelicans is a local runtime. It does not require provider API keys for the default model path. Each category maps to a Hugging Face model ID and the agent loads that model locally through Transformers when the agent is activated.

Recommended starter models:

| Category | Model | Why |
| --- | --- | --- |
| General text | `Qwen/Qwen2.5-1.5B-Instruct` | Small instruction model for normal chat and project help. |
| Reasoning | `Qwen/Qwen2.5-1.5B-Instruct` | Lightweight default reasoning model for CPU or smaller GPU experiments. |
| Coding | `Qwen/Qwen2.5-Coder-1.5B-Instruct` | Small coding-focused model for implementation and test tasks. |
| Vision | `Qwen/Qwen2.5-VL-3B-Instruct` | Vision-language model for image and UI understanding workflows. |

### Manual download

If you want full control, manually download models with the Hugging Face CLI or your preferred cache location, then set each agent `model` field in `tropelicans.config.json` to the local directory path or Hugging Face model ID.

```bash
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct
```

### Automatic download

If you want a faster setup, install the Hugging Face extra and let Tropelicans download one model category or all recommended models into the Hugging Face cache.

```bash
pip install -e ".[huggingface]"
tropelicans models list
tropelicans models download coding
tropelicans models download all
```

The model is still local after download. Tropelicans uses the Hugging Face cache and does not call a hosted inference API. The `echo` backend exists only as a lightweight test backend; normal runtime configuration uses the `huggingface` backend.
