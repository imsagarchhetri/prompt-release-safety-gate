"""The AI feature under test: messy customer note -> structured CRM summary."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from .llm import get_llm
from .schemas import CRMSummary, PromptConfig, cost_usd


@dataclass
class FeatureOutput:
    parsed: CRMSummary | None
    raw: str
    schema_valid: bool
    cost_usd: float
    latency_ms: float
    tokens: int
    error: str | None = None


def run_feature(note: str, cfg: PromptConfig) -> FeatureOutput:
    import time
    user = (f"Customer note:\n{note}\n\n"
            "Return ONLY JSON with keys: summary, sentiment "
            "(positive|neutral|negative), next_action, urgency (low|medium|high), "
            "confidence (0-1).")
    start = time.perf_counter()
    r = get_llm().complete(system=cfg.system_prompt, user=user, model=cfg.model,
                           temperature=cfg.temperature, json_mode=True)
    latency = (time.perf_counter() - start) * 1000
    cost = cost_usd(cfg.model, r.prompt_tokens, r.completion_tokens)

    try:
        parsed = CRMSummary(**json.loads(r.text))
        return FeatureOutput(parsed, r.text, True, cost, latency,
                             r.prompt_tokens + r.completion_tokens)
    except (ValidationError, json.JSONDecodeError) as e:
        return FeatureOutput(None, r.text, False, cost, latency,
                             r.prompt_tokens + r.completion_tokens, str(e)[:160])
