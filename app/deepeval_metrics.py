"""Optional DeepEval integration.

Defines DeepEval custom metrics (subclassing BaseMetric) that are deterministic —
no judge LLM required — so they run in CI without keys. This lets teams that
standardize on DeepEval consume the same scoring used by the native gate.

    from app.deepeval_metrics import build_test_cases, SchemaValidityMetric
"""
from __future__ import annotations

import json

try:
    from deepeval.metrics import BaseMetric
    from deepeval.test_case import LLMTestCase
    _HAS_DEEPEVAL = True
except Exception:  # pragma: no cover
    _HAS_DEEPEVAL = False
    BaseMetric = object  # type: ignore


def build_test_cases(cases, cfg):
    """Run the feature and wrap each result as a DeepEval LLMTestCase."""
    from .feature import run_feature
    if not _HAS_DEEPEVAL:
        raise RuntimeError("deepeval not installed")
    tcs = []
    for c in cases:
        out = run_feature(c["note"], cfg)
        tc = LLMTestCase(
            input=c["note"],
            actual_output=out.raw,
            expected_output=json.dumps({k: c.get(k) for k in
                                        ("sentiment", "urgency", "next_action")}),
            metadata={"schema_valid": out.schema_valid,
                      "parsed": out.parsed.model_dump() if out.parsed else None,
                      "expected": c, "forbidden": c.get("forbidden", [])},
        )
        tcs.append(tc)
    return tcs


def _meta(test_case) -> dict:
    # `metadata` (new) with fallback to `additional_metadata` (older DeepEval)
    return getattr(test_case, "metadata", None) or getattr(
        test_case, "additional_metadata", {}) or {}


class SchemaValidityMetric(BaseMetric):
    """1.0 if the output validated against the CRM schema, else 0.0."""
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case) -> float:
        ok = bool(_meta(test_case).get("schema_valid"))
        self.score = 1.0 if ok else 0.0
        self.success = self.score >= self.threshold
        self.reason = "schema valid" if ok else "schema invalid"
        return self.score

    async def a_measure(self, test_case) -> float:  # noqa: D401
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "SchemaValidity"


class FieldAccuracyMetric(BaseMetric):
    """Fraction of (sentiment, urgency, next_action) fields matching the label."""
    def __init__(self, threshold: float = 0.66):
        self.threshold = threshold

    def measure(self, test_case) -> float:
        meta = _meta(test_case)
        parsed, exp = meta.get("parsed"), meta.get("expected", {})
        if not parsed:
            self.score, self.success, self.reason = 0.0, False, "no parsed output"
            return 0.0
        keys = ["sentiment", "urgency", "next_action"]
        hits = 0
        for k in keys:
            e = exp.get(k)
            if e is None:
                hits += 1
            elif k == "next_action":
                hits += int(e.lower() in str(parsed[k]).lower())
            else:
                hits += int(parsed[k] == e)
        self.score = hits / len(keys)
        self.success = self.score >= self.threshold
        self.reason = f"{hits}/{len(keys)} fields correct"
        return self.score

    async def a_measure(self, test_case) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "FieldAccuracy"
