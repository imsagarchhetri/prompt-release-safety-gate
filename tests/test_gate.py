from app.gate import decide
from app.runner import load_golden, run_prompt


def test_identical_prompts_pass():
    cases = load_golden()
    base = run_prompt("v1_production", cases)
    cand = run_prompt("v1_production", cases)
    d = decide(base, cand)
    assert d.verdict == "PASS"
    assert d.exit_code == 0


def test_pricier_candidate_fails_on_cost():
    cases = load_golden()
    base = run_prompt("v1_production", cases)
    cand = run_prompt("v2_candidate", cases)
    d = decide(base, cand)
    assert d.verdict == "FAIL"
    assert d.exit_code == 1
    assert any("cost" in r for r in d.reasons)


def test_schema_validity_is_measured():
    cases = load_golden()
    base = run_prompt("v1_production", cases)
    assert 0.0 <= base.schema_valid <= 1.0
    assert base.schema_valid == 1.0   # test provider always returns valid JSON
