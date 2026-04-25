"""Slack alerting (no-op if no webhook configured)."""
from __future__ import annotations

from .config import get_settings
from .gate import Decision


def notify_slack(decision: Decision, base: str, cand: str) -> bool:
    url = get_settings().slack_webhook_url
    if not url:
        return False
    import requests
    emoji = {"PASS": ":white_check_mark:", "WARN": ":warning:", "FAIL": ":no_entry:"}
    text = (f"{emoji.get(decision.verdict, '')} Prompt gate *{decision.verdict}* "
            f"for `{cand}` vs `{base}`")
    if decision.reasons:
        text += "\n" + "\n".join(f"• {r}" for r in decision.reasons)
    try:
        requests.post(url, json={"text": text}, timeout=10)
        return True
    except Exception:
        return False
