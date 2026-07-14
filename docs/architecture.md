# Tropelicans Architecture

This document describes the first architecture direction for Tropelicans.

## Runtime orchestrator

The runtime orchestrator is the center of the framework. It receives user input from the CLI or web view, decides which capabilities are needed, and coordinates agents, memory, workspace tools, and skills.

Responsibilities:

- keep the default runtime lightweight
- activate specialized agents only when needed
- route tasks to the right model or tool
- enforce user configuration and permission policies
- summarize completed work back into memory when useful

## Agent router

The agent router maps task categories to local Hugging Face model-backed agents. A default text agent is always available. Other agents are inactive until a task requires them or the user enables them.

Example categories:

| Category | Purpose |
| --- | --- |
| Reasoning | planning, decomposition, complex decisions |
| Coding | code generation, refactoring, test repair |
| Vision | image and photo understanding |
| Research | retrieval, reading, source synthesis |
| Debugging | test failure analysis and fix recommendations |

Agents can collaborate through the orchestrator instead of all being loaded at the same time. Hugging Face models are loaded lazily when their category is selected, which keeps memory and compute usage lower than always-on multi-agent systems.

## Workspace manager

The workspace manager gives the runtime controlled access to the user's project files and commands. It tracks whether files were changed by the AI or by the user, so the AI can infer user intent from later edits.

Responsibilities:

- index workspace files
- detect user-made changes
- expose safe tool execution
- connect workspace context to memory
- support project-specific configuration

## Memory manager

The memory manager separates temporary context from durable knowledge.

Memory types:

- **Working memory:** active task context that can be discarded after completion.
- **Session memory:** useful information for the current CLI or web session.
- **Project memory:** durable project-specific knowledge.
- **User memory:** durable user preferences and repeated behavior.
- **Incident memory:** bugs, test failures, fixes, and debugging outcomes.

The memory manager should score importance, deduplicate similar entries, expire low-value context, and allow the user to inspect or edit stored memory.

## Skills system

Skills are reusable capabilities that can be created by users or by the AI. A skill can package instructions, scripts, templates, prompts, or tool workflows.

A skill should define:

- name and description
- when it should be used
- required tools or permissions
- reusable workflow instructions
- optional scripts or assets

## Web view

The web view is the visual control plane for the runtime.

Initial screens should include:

- onboarding
- agent configuration
- memory and knowledge browser
- workspace overview
- skills manager
- runtime activity monitor
