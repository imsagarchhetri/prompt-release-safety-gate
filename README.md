# Project 2 — Prompt Release Safety Gate (Production)

**Topic:** LLMOps · PromptOps · CI/CD · Regression Testing · Evals

A CI gate that runs a regression suite whenever a prompt changes, compares the
**candidate** prompt against the current **production** prompt, and **blocks the
merge** (non-zero exit) if quality, cost, latency, or safety degrade past a
threshold. Posts a Markdown/HTML report to the PR.


## Real stack

| Concern | Tool |
|---|---|
| Prompt format | versioned **YAML** (`prompts/*.yaml`) |
| Structured output | **Pydantic** (`app/schemas.py::CRMSummary`) |
| Eval runner | custom multi-dimensional + **DeepEval** custom metrics (`app/deepeval_metrics.py`) |
| Storage | **SQLite** + JSON artifacts (`app/storage.py`) |
| Reporting | **Markdown + HTML** via Jinja2 (`app/report.py`) |
| CI/CD | **GitHub Actions** (`.github/workflows/prompt-gate.yml`) |
| Alerting | **Slack webhook** (`app/alert.py`) |
| LLM | OpenAI / Anthropic / Ollama + keyless `test` provider |
| Tests | **pytest** (`tests/`) |

The feature under test: messy customer note → structured CRM summary, validated
with Pydantic. Runs **keyless** by default (`llm_provider=test` returns a
content-aware, PII-redacting CRM summary so quality/cost/safety scoring is real).

## Quickstart (no keys)

```bash
cd 02-prompt-release-safety-gate
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m app.cli --baseline v1_production --candidate v2_candidate   # FAIL demo
python -m app.cli --baseline v1_production --candidate v1_production   # PASS
python -m app.cli --baseline v1_production --candidate v2_candidate --deepeval
echo "exit code: $?"      # 1 on FAIL → blocks CI
pytest                    # 7 tests
```

## Demo result

The included candidate switches to a pricier model (`gpt-4o` vs `gpt-4o-mini`)
and a verbose prompt. The gate catches it:

```
# Prompt Release Gate — FAIL
| Metric         | Baseline | Candidate |
| Schema valid   | 100.0%   | 100.0%    |
| Field accuracy | 60.0%    | 60.0%     |
| Avg cost (USD) | 0.000040 | 0.000670  |
Blocking reasons:
- avg cost rose 1567% (>20%)
VERDICT: FAIL (exit 1)
```

Field accuracy is real (content-aware `test` provider matched against golden
labels); the cost gate is exact because cost is computed from the model price
table — so it works identically with `llm_provider=openai`.

## Thresholds

Edit `Thresholds` in `app/config.py` (env-overridable): `schema_valid_drop` (2pp),
`field_acc_drop` (5pp), `cost_rise_pct` (20%), `latency_rise_pct` (50%),
`safety_regressions` (0).

## What's verified vs. needs infra

-  **Verified keyless here:** gate logic, multi-dim scoring, FAIL/PASS exit
  codes, DeepEval custom metrics, MD/HTML report, SQLite history, 7 pytest.
-  **Needs setup:** real LLM scoring (`llm_provider=openai` + key), Slack alerts
  (`slack_webhook_url`), and the GitHub Action posting on real PRs.


