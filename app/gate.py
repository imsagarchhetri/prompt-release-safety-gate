"""The release decision: compare candidate to baseline against thresholds."""
from __future__ import annotations

from dataclasses import dataclass

from .config import get_settings
from .metrics import RunSummary


@dataclass
class Decision:
    verdict: str            # PASS | WARN | FAIL
    reasons: list[str]
    warnings: list[str]
    metrics_delta: dict

    @property
    def exit_code(self) -> int:
        return 1 if self.verdict == "FAIL" else 0


def decide(base: RunSummary, cand: RunSummary) -> Decision:
    t = get_settings().thresholds
    reasons, warnings = [], []

    cost_rise = (cand.avg_cost - base.avg_cost) / (base.avg_cost or 1e-9)
    lat_rise = (cand.avg_latency - base.avg_latency) / (base.avg_latency or 1e-9)
    delta = {
        "schema_valid": (base.schema_valid, cand.schema_valid),
        "field_acc": (base.field_acc, cand.field_acc),
        "avg_cost": (base.avg_cost, cand.avg_cost),
        "avg_latency": (base.avg_latency, cand.avg_latency),
        "safety_fails": (base.safety_fails, cand.safety_fails),
        "cost_rise_pct": cost_rise,
        "latency_rise_pct": lat_rise,
    }

    # blocking conditions
    if base.schema_valid - cand.schema_valid > t.schema_valid_drop:
        reasons.append(f"schema validity dropped {base.schema_valid:.2f}->{cand.schema_valid:.2f}")
    if base.field_acc - cand.field_acc > t.field_acc_drop:
        reasons.append(f"field accuracy dropped {base.field_acc:.2f}->{cand.field_acc:.2f}")
    if cost_rise > t.cost_rise_pct:
        reasons.append(f"avg cost rose {cost_rise*100:.0f}% (>{t.cost_rise_pct*100:.0f}%)")
    if lat_rise > t.latency_rise_pct:
        reasons.append(f"avg latency rose {lat_rise*100:.0f}%")
    if cand.safety_fails > base.safety_fails + t.safety_regressions:
        reasons.append(f"safety regressions {base.safety_fails}->{cand.safety_fails}")

    if reasons:
        return Decision("FAIL", reasons, warnings, delta)

    # warning conditions (non-blocking)
    if base.field_acc - cand.field_acc > t.warn_field_acc_drop:
        warnings.append("minor field-accuracy dip")
    if cost_rise > t.warn_cost_rise_pct:
        warnings.append(f"cost up {cost_rise*100:.0f}%")
    return Decision("WARN" if warnings else "PASS", reasons, warnings, delta)
