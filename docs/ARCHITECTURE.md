# Architecture

```
 PR changes prompts/** ──► GitHub Action (paths filter)
                              │
                          app.cli
                              │
   prompts/v1_production.yaml ─┐
   prompts/v2_candidate.yaml  ─┤ load_prompt (Pydantic PromptConfig)
   data/golden.jsonl ─────────┤
                              ▼
                   runner.run_prompt(baseline)   runner.run_prompt(candidate)
                      │ feature.run_feature (LLM → CRMSummary, telemetry)
                      │ metrics.score_case  (schema, field acc, safety, cost, latency)
                      ▼                                  ▼
                  RunSummary(base)                  RunSummary(cand)
                              │   diff_cases(base, cand)
                              ▼
                   gate.decide  ──► Decision{PASS|WARN|FAIL, reasons, exit_code}
                              │
        ┌─────────────────────┼─────────────────────┬───────────────┐
   report.write_reports   storage.save_run      alert.notify_slack   exit(code)
   (md + html, Jinja2)    (SQLite history)      (webhook)            (1 = block)
```

## Key decisions

### Multi-dimensional scoring
Schema validity, field accuracy, safety (PII leak), cost, and latency are scored
**separately**. Collapsing to a single number too early hides the regression that
matters. The gate maps each dimension to its own blocking/warning threshold.

### Cost is computed, not guessed
`schemas.cost_usd` uses a public price table, so the cost-regression gate is exact
regardless of LLM provider — a verbose or pricier candidate is caught even in the
keyless `test` mode (where token counts are estimated from text length).

### Keyless `test` provider that's actually useful
`llm.LLMClient._test` derives sentiment/urgency from the note and **redacts PII**,
so field accuracy is meaningful and a baseline doesn't spuriously trip the safety
check. This makes CI runnable and deterministic without API keys; flip
`llm_provider` for real scoring.

### DeepEval as an optional, deterministic adapter
`deepeval_metrics.py` wraps the same scoring as DeepEval `BaseMetric` subclasses
(no judge LLM), so teams standardizing on DeepEval get identical results in CI
without keys. Guarded by import so the core never hard-depends on it.

### Reproducible runner
The same `Dockerfile` image runs locally and in the GitHub Action, with all
behavior controlled by env vars (provider, thresholds, paths).

## Extending
- Add dimensions in `metrics.py` (e.g. an LLM-judge relevance score) and a
  matching threshold in `config.Thresholds`.
- Add prompt versions in `prompts/`; the runner compares any two by name.
- Swap the feature: change `CRMSummary` + the `feature.run_feature` user prompt.
```
