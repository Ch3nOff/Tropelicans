"""Command line interface for Tropelicans."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from pathlib import Path

from .config import config_to_dict, default_config
from .models import RECOMMENDED_MODELS, download_model
from .runtime import TropelicansRuntime
from .skills import Skill
from .web import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and customize the Tropelicans AI runtime.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace directory to inspect and manage.")
    parser.add_argument("--config", type=Path, help="Path to a Tropelicans JSON config file.")
    parser.add_argument("--no-open", action="store_true", help="Do not try to open the web view in a browser.")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Send a prompt through the runtime.")
    run.add_argument("prompt")
    run.add_argument("--category", help="Agent category or agent name to route to.")

    sub.add_parser("status", help="Show runtime status.")
    sub.add_parser("init", help="Create a default tropelicans.config.json in the workspace.")

    remember = sub.add_parser("remember", help="Store a memory entry.")
    remember.add_argument("content")
    remember.add_argument("--scope", default="project")
    remember.add_argument("--importance", type=float, default=0.7)
    remember.add_argument("--tag", action="append", default=[])

    skill = sub.add_parser("skill", help="Create a reusable skill.")
    skill.add_argument("name")
    skill.add_argument("description")
    skill.add_argument("trigger")
    skill.add_argument("instructions")

    models = sub.add_parser("models", help="List or download recommended local Hugging Face models.")
    models_sub = models.add_subparsers(dest="models_command", required=True)
    models_sub.add_parser("list", help="List recommended model IDs by category.")
    download = models_sub.add_parser("download", help="Download one recommended model or all models into the Hugging Face cache.")
    download.add_argument("category", choices=[*RECOMMENDED_MODELS.keys(), "all"])
    download.add_argument("--cache-dir", type=Path)

    start = sub.add_parser("start", help="Create config if needed and start the local web chat view.")
    start.add_argument("--host")
    start.add_argument("--port", type=int)

    web = sub.add_parser("web", help="Start the local web chat view.")
    web.add_argument("--host")
    web.add_argument("--port", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.workspace.mkdir(parents=True, exist_ok=True)
    if args.command is None:
        args.command = "start"
        args.host = None
        args.port = None

    if args.command == "init":
        config_path = args.workspace / "tropelicans.config.json"
        config_path.write_text(json.dumps(config_to_dict(default_config()), indent=2), encoding="utf-8")
        print(f"Created {config_path}")
        return 0

    if args.command in {"web", "start"}:
        config_path = args.config or args.workspace / "tropelicans.config.json"
        if args.command == "start" and not config_path.exists():
            config_path.write_text(json.dumps(config_to_dict(default_config()), indent=2), encoding="utf-8")
            print(f"Created {config_path}")
        if not args.no_open:
            host = args.host or "127.0.0.1"
            port = args.port or 8765
            threading.Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
        serve(args.workspace, config_path if config_path.exists() else args.config, args.host, args.port)
        return 0

    if args.command == "models":
        if args.models_command == "list":
            print(json.dumps(RECOMMENDED_MODELS, indent=2))
            return 0
        categories = RECOMMENDED_MODELS.keys() if args.category == "all" else [args.category]
        downloaded = {category: str(download_model(RECOMMENDED_MODELS[category], args.cache_dir)) for category in categories}
        print(json.dumps(downloaded, indent=2))
        return 0

    runtime = TropelicansRuntime(args.workspace, args.config)

    if args.command == "status":
        print(json.dumps({
            "workspace": str(runtime.workspace),
            "activeAgents": runtime.router.active_agents(),
            "memoryEntries": len(runtime.memory.list()),
            "skills": [skill.name for skill in runtime.skills.list()],
        }, indent=2))
        return 0

    if args.command == "remember":
        entry = runtime.memory.remember(args.scope, args.content, args.importance, args.tag)
        print(json.dumps(entry.__dict__, indent=2))
        return 0

    if args.command == "skill":
        path = runtime.skills.create(Skill(args.name, args.description, args.trigger, args.instructions))
        print(f"Created skill {path}")
        return 0

    if args.command == "run":
        result = runtime.run(args.prompt, args.category)
        print(result.response.text)
        print(json.dumps({
            "agent": result.response.agent,
            "activeAgents": result.active_agents,
            "workspaceChanges": [change.__dict__ for change in result.workspace_changes],
            "matchedSkills": result.matched_skills,
        }, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
