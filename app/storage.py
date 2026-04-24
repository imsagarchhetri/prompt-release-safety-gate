"""Persist runs + decisions to SQLite (portable, inspectable audit trail)."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import get_settings
from .gate import Decision
from .metrics import RunSummary


def _conn() -> sqlite3.Connection:
    path = Path(get_settings().db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS gate_runs(
        ts REAL, baseline TEXT, candidate TEXT, verdict TEXT,
        reasons TEXT, metrics TEXT)""")
    return con


def save_run(base: RunSummary, cand: RunSummary, decision: Decision) -> None:
    con = _conn()
    con.execute("INSERT INTO gate_runs VALUES(?,?,?,?,?,?)",
                (time.time(), base.version, cand.version, decision.verdict,
                 json.dumps(decision.reasons), json.dumps(decision.metrics_delta)))
    con.commit()
    con.close()


def history(limit: int = 20) -> list[dict]:
    con = _conn()
    rows = con.execute(
        "SELECT ts, baseline, candidate, verdict, reasons FROM gate_runs "
        "ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [{"ts": r[0], "baseline": r[1], "candidate": r[2], "verdict": r[3],
             "reasons": json.loads(r[4])} for r in rows]
