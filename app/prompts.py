"""Load versioned YAML prompts."""
from __future__ import annotations

from pathlib import Path

import yaml

from .config import get_settings
from .schemas import PromptConfig


def load_prompt(version: str) -> PromptConfig:
    path = Path(get_settings().prompts_dir) / f"{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {path}")
    return PromptConfig(**yaml.safe_load(path.read_text()))
