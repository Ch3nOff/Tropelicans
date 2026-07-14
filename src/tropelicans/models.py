"""Local Hugging Face model loading and download helpers."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RECOMMENDED_MODELS: dict[str, str] = {
    "general": "Qwen/Qwen2.5-1.5B-Instruct",
    "reasoning": "Qwen/Qwen2.5-1.5B-Instruct",
    "coding": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "vision": "Qwen/Qwen2.5-VL-3B-Instruct",
}

RECOMMENDED_TASKS: dict[str, str] = {
    "general": "text-generation",
    "reasoning": "text-generation",
    "coding": "text-generation",
    "vision": "image-text-to-text",
}


@dataclass(frozen=True)
class GenerationOptions:
    max_new_tokens: int = 256
    temperature: float = 0.7
    device: str = "auto"


class MissingOptionalDependencyError(RuntimeError):
    """Raised when local model execution dependencies are not installed."""


class LocalModelRunner:
    """Lazy local inference wrapper for Hugging Face Transformers models."""

    def __init__(self, model_id: str, task: str = "text-generation", options: GenerationOptions | None = None) -> None:
        self.model_id = model_id
        self.task = task
        self.options = options or GenerationOptions()
        self._pipeline: Any | None = None

    def generate(self, prompt: str) -> str:
        pipeline = self._load_pipeline()
        output = pipeline(
            prompt,
            max_new_tokens=self.options.max_new_tokens,
            temperature=self.options.temperature,
            do_sample=self.options.temperature > 0,
        )
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, dict):
                return str(first.get("generated_text", first))
        return str(output)

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        if importlib.util.find_spec("transformers") is None:
            raise MissingOptionalDependencyError(
                "Local model execution requires transformers. Install with: pip install 'tropelicans[huggingface]'"
            )
        from transformers import pipeline

        kwargs: dict[str, Any] = {"model": self.model_id, "task": self.task}
        if self.options.device != "auto":
            kwargs["device"] = self.options.device
        self._pipeline = pipeline(**kwargs)
        return self._pipeline


def download_model(model_id: str, cache_dir: Path | None = None) -> Path:
    """Download a model snapshot into the Hugging Face cache and return its local path."""

    if importlib.util.find_spec("huggingface_hub") is None:
        raise MissingOptionalDependencyError(
            "Automatic model download requires huggingface_hub. Install with: pip install 'tropelicans[huggingface]'"
        )
    from huggingface_hub import snapshot_download

    downloaded = snapshot_download(repo_id=model_id, cache_dir=str(cache_dir) if cache_dir else None)
    return Path(downloaded)
