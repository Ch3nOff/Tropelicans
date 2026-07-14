from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from tropelicans.config import default_config
from tropelicans.models import RECOMMENDED_MODELS
from tropelicans.runtime import TropelicansRuntime
from tropelicans.skills import Skill


def write_echo_config(root: Path) -> Path:
    config = {
        "runtime": {"defaultAgent": "text", "lazyAgentActivation": True},
        "agents": {
            "text": {"category": "general", "model": "test-text", "activeByDefault": True, "backend": "echo"},
            "coding": {"category": "coding", "model": "test-coding", "activeByDefault": False, "backend": "echo"},
        },
    }
    path = root / "tropelicans.config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


class RuntimeTests(unittest.TestCase):
    def test_default_config_uses_local_hugging_face_models(self):
        config = default_config()
        self.assertTrue(config.agents["text"].active_by_default)
        self.assertFalse(config.agents["coding"].active_by_default)
        self.assertEqual(config.agents["coding"].backend, "huggingface")
        self.assertEqual(config.agents["coding"].model, RECOMMENDED_MODELS["coding"])

    def test_runtime_lazy_activates_category_agent(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = TropelicansRuntime(root, write_echo_config(root))
            self.assertEqual(runtime.router.active_agents(), ["text"])
            result = runtime.run("write tests", category="coding")
            self.assertEqual(result.response.agent, "coding")
            self.assertIn("coding", result.active_agents)

    def test_runtime_records_workspace_changes_and_matches_skills(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = TropelicansRuntime(root, write_echo_config(root))
            runtime.skills.create(Skill("debug-tests", "Debug tests", "test", "Inspect failing tests."))
            (root / "app.py").write_text("print('hello')", encoding="utf-8")
            result = runtime.run("test the workspace")
            self.assertEqual(result.matched_skills, ["debug-tests"])
            self.assertEqual(result.workspace_changes[0].status, "added")
            self.assertTrue(runtime.memory.search("workspace changes"))


if __name__ == "__main__":
    unittest.main()
