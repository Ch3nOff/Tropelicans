# Local Hugging Face Models

Tropelicans is designed to run models locally instead of requiring hosted model API keys. Agent configuration maps each runtime category to a Hugging Face model ID or a local model directory.

## Recommended starter models

| Category | Default model | Task |
| --- | --- | --- |
| General text | `Qwen/Qwen2.5-1.5B-Instruct` | `text-generation` |
| Reasoning | `Qwen/Qwen2.5-1.5B-Instruct` | `text-generation` |
| Coding | `Qwen/Qwen2.5-Coder-1.5B-Instruct` | `text-generation` |
| Vision | `Qwen/Qwen2.5-VL-3B-Instruct` | `image-text-to-text` |

These defaults are intentionally small enough for early local experiments. Users can replace them with larger local models in `tropelicans.config.json` as their hardware allows.

## Manual download workflow

Manual download gives the user full control over storage location, revisions, and quantization choices.

```bash
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct
```

After downloading, set the agent `model` field to either the Hugging Face model ID or a local path.

## Automatic download workflow

For faster setup, install the Hugging Face optional dependencies and use the built-in model downloader.

```bash
pip install -e ".[huggingface]"
tropelicans models list
tropelicans models download coding
tropelicans models download all
```

The downloader uses the Hugging Face cache. Once downloaded, inference remains local and does not call a hosted inference API.

## Runtime behavior

- The default text agent is active at startup.
- Specialized agents stay inactive until selected by category.
- The first call to a Hugging Face-backed agent lazily loads the local model.
- The `echo` backend exists for tests and debugging only.
