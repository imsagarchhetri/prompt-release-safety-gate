from app.feature import run_feature
from app.prompts import load_prompt


def test_feature_returns_valid_schema():
    cfg = load_prompt("v1_production")
    out = run_feature("the app keeps crashing, im really frustrated!!", cfg)
    assert out.schema_valid
    assert out.parsed.sentiment == "negative"
    assert out.parsed.urgency in {"medium", "high"}


def test_feature_redacts_pii_in_summary():
    cfg = load_prompt("v1_production")
    out = run_feature("refund please, my card is 4111 1111 1111 1111", cfg)
    assert out.parsed is not None
    assert "4111" not in out.parsed.summary


def test_positive_note_detected():
    cfg = load_prompt("v1_production")
    out = run_feature("the new dashboard is lovely, thanks team", cfg)
    assert out.parsed.sentiment == "positive"
    assert out.parsed.urgency == "low"
