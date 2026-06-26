from __future__ import annotations

from functools import lru_cache
from importlib.resources import files

PROMPT_PACKAGE = "pdf2obsidian.prompts"
PROMPT_SUFFIX = ".txt"


@lru_cache(maxsize=16)
def load_prompt(prompt_name: str) -> str:
    """Load a packaged prompt by name without allowing path traversal."""
    if not prompt_name or "/" in prompt_name or "\\" in prompt_name or ".." in prompt_name:
        raise ValueError(f"Invalid prompt name: {prompt_name!r}")

    file_name = prompt_name if prompt_name.endswith(PROMPT_SUFFIX) else f"{prompt_name}.txt"
    prompt_path = files(PROMPT_PACKAGE).joinpath(file_name)
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file was not found: {file_name}")
    return prompt_path.read_text(encoding="utf-8").strip()

