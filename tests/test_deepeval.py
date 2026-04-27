import pytest

deepeval = pytest.importorskip("deepeval")

from app.deepeval_metrics import (build_test_cases, SchemaValidityMetric,  # noqa: E402
                                  FieldAccuracyMetric)
from app.prompts import load_prompt  # noqa: E402
from app.runner import load_golden  # noqa: E402


def test_deepeval_custom_metrics_run_keyless():
    cases = load_golden()
    tcs = build_test_cases(cases, load_prompt("v1_production"))
    assert len(tcs) == len(cases)

    schema = SchemaValidityMetric()
    field = FieldAccuracyMetric()
    schema_scores = [schema.measure(tc) for tc in tcs]
    field_scores = [field.measure(tc) for tc in tcs]

    assert all(s == 1.0 for s in schema_scores)        # test provider -> valid JSON
    assert sum(field_scores) / len(field_scores) > 0.3  # meaningful field accuracy
