"""Regression runner: run baseline + candidate prompts over the golden set."""
from __future__ import annotations

import json
from pathlib import Path

from .config import get_settings
from .feature import run_feature
from .metrics import CaseScore, RunSummary, score_case, summarize
from .prompts import load_prompt


def load_golden() -> list[dict]:
    path = Path(get_settings().golden_path)
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def run_prompt(version: str, cases: list[dict]) -> RunSummary:
    cfg = load_prompt(version)
    scores: list[CaseScore] = []
    for c in cases:
        out = run_feature(c["note"], cfg)
        scores.append(score_case(c, out))
    return summarize(version, scores)


def diff_cases(base: RunSummary, cand: RunSummary) -> dict:
    """Per-case run-over-run diff: regressions, improvements, new safety fails."""
    bmap = {s.case_id: s for s in base.cases}
    regressions, improvements, new_safety = [], [], []
    for cs in cand.cases:
        bs = bmap.get(cs.case_id)
        if not bs:
            continue
        if cs.field_accuracy < bs.field_accuracy or (bs.schema_valid and not cs.schema_valid):
            regressions.append(cs.case_id)
        if cs.field_accuracy > bs.field_accuracy:
            improvements.append(cs.case_id)
        if cs.safety_fail and not bs.safety_fail:
            new_safety.append(cs.case_id)
    return {"regressions": regressions, "improvements": improvements,
            "new_safety_failures": new_safety}
