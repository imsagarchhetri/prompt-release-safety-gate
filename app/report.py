"""Render the release report as Markdown (PR comment) and HTML (browser artifact)."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from .config import get_settings
from .gate import Decision
from .metrics import RunSummary

_MD = Template("""# Prompt Release Gate — **{{ d.verdict }}**

Baseline `{{ base.version }}`  →  Candidate `{{ cand.version }}`

| Metric | Baseline | Candidate |
|---|---|---|
| Schema valid | {{ '%.1f'|format(base.schema_valid*100) }}% | {{ '%.1f'|format(cand.schema_valid*100) }}% |
| Field accuracy | {{ '%.1f'|format(base.field_acc*100) }}% | {{ '%.1f'|format(cand.field_acc*100) }}% |
| Avg cost (USD) | {{ '%.6f'|format(base.avg_cost) }} | {{ '%.6f'|format(cand.avg_cost) }} |
| Avg latency (ms) | {{ '%.1f'|format(base.avg_latency) }} | {{ '%.1f'|format(cand.avg_latency) }} |
| Safety fails | {{ base.safety_fails }} | {{ cand.safety_fails }} |

{% if d.reasons %}**Blocking reasons:**
{% for r in d.reasons %}- {{ r }}
{% endfor %}{% endif %}{% if d.warnings %}**Warnings:**
{% for w in d.warnings %}- {{ w }}
{% endfor %}{% endif %}{% if diff.regressions %}**Regressed cases:** {{ diff.regressions|join(', ') }}
{% endif %}{% if diff.new_safety_failures %}**New safety failures:** {{ diff.new_safety_failures|join(', ') }}
{% endif %}""")

_HTML = Template("""<!doctype html><html><head><meta charset="utf-8">
<title>Prompt Release Gate — {{ d.verdict }}</title>
<style>body{font-family:system-ui;margin:2rem;max-width:780px}
.v{padding:.3rem .8rem;border-radius:6px;color:#fff;font-weight:700}
.PASS{background:#16a34a}.WARN{background:#d97706}.FAIL{background:#dc2626}
table{border-collapse:collapse;width:100%;margin:1rem 0}
td,th{border:1px solid #ddd;padding:.5rem;text-align:left}</style></head><body>
<h1>Prompt Release Gate <span class="v {{ d.verdict }}">{{ d.verdict }}</span></h1>
<p>Baseline <code>{{ base.version }}</code> → Candidate <code>{{ cand.version }}</code></p>
<table><tr><th>Metric</th><th>Baseline</th><th>Candidate</th></tr>
<tr><td>Schema valid</td><td>{{ '%.1f'|format(base.schema_valid*100) }}%</td><td>{{ '%.1f'|format(cand.schema_valid*100) }}%</td></tr>
<tr><td>Field accuracy</td><td>{{ '%.1f'|format(base.field_acc*100) }}%</td><td>{{ '%.1f'|format(cand.field_acc*100) }}%</td></tr>
<tr><td>Avg cost (USD)</td><td>{{ '%.6f'|format(base.avg_cost) }}</td><td>{{ '%.6f'|format(cand.avg_cost) }}</td></tr>
<tr><td>Avg latency (ms)</td><td>{{ '%.1f'|format(base.avg_latency) }}</td><td>{{ '%.1f'|format(cand.avg_latency) }}</td></tr>
<tr><td>Safety fails</td><td>{{ base.safety_fails }}</td><td>{{ cand.safety_fails }}</td></tr></table>
{% if d.reasons %}<h3>Blocking reasons</h3><ul>{% for r in d.reasons %}<li>{{ r }}</li>{% endfor %}</ul>{% endif %}
{% if d.warnings %}<h3>Warnings</h3><ul>{% for w in d.warnings %}<li>{{ w }}</li>{% endfor %}</ul>{% endif %}
</body></html>""")


def write_reports(base: RunSummary, cand: RunSummary, d: Decision, diff: dict) -> dict:
    out_dir = Path(get_settings().report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = _MD.render(base=base, cand=cand, d=d, diff=diff)
    html = _HTML.render(base=base, cand=cand, d=d)
    (out_dir / "report.md").write_text(md)
    (out_dir / "report.html").write_text(html)
    return {"markdown": md, "md_path": str(out_dir / "report.md"),
            "html_path": str(out_dir / "report.html")}
