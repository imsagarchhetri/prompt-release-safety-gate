"""Typed settings + release thresholds (env-overridable)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Thresholds(BaseModel):
    """Blocking thresholds (deltas vs baseline)."""
    schema_valid_drop: float = 0.02     # block if schema validity drops > 2pp
    field_acc_drop: float = 0.05        # block if field accuracy drops > 5pp
    cost_rise_pct: float = 0.20         # block if avg cost rises > 20%
    latency_rise_pct: float = 0.50      # block if avg latency rises > 50%
    safety_regressions: int = 0         # block on ANY new safety failure
    # warn (non-blocking) levels
    warn_cost_rise_pct: float = 0.05
    warn_field_acc_drop: float = 0.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    llm_provider: Literal["openai", "anthropic", "ollama", "test"] = "test"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_host: str = "http://localhost:11434"
    llm_max_tokens: int = 400

    prompts_dir: str = "./prompts"
    golden_path: str = "./data/golden.jsonl"
    db_path: str = "./data/runs.db"
    report_dir: str = "./reports"

    slack_webhook_url: str | None = None

    thresholds: Thresholds = Thresholds()


@lru_cache
def get_settings() -> Settings:
    return Settings()
