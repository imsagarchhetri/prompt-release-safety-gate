"""LLM providers behind one interface (openai/anthropic/ollama + test double).

The `test` provider returns a deterministic, content-aware CRM summary so the
gate's quality/cost/safety scoring is exercised for real without API keys. It
redacts obvious PII (so a baseline doesn't trip the safety check) and derives
sentiment/urgency from the note text, giving meaningful field accuracy.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .config import get_settings

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
CARD = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

NEG = ("frustrat", "angry", "unacceptable", "deleted", "lost", "twice", "refund",
       "crash", "locked", "wait", "still")
URGENT = ("urgent", "asap", "immediately", "now", "20 min", "demo", "outage", "locked")


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int


class LLMClient:
    def __init__(self):
        self.s = get_settings()

    def complete(self, *, system: str, user: str, model: str, temperature: float,
                 json_mode: bool = True) -> LLMResult:
        p = self.s.llm_provider
        if p == "openai":
            return self._openai(system, user, model, temperature, json_mode)
        if p == "anthropic":
            return self._anthropic(system, user, model, temperature)
        if p == "ollama":
            return self._ollama(system, user, model, temperature, json_mode)
        return self._test(system, user)

    def _openai(self, system, user, model, temperature, json_mode):
        from openai import OpenAI
        client = OpenAI()
        kw = dict(model=model, temperature=temperature, max_tokens=self.s.llm_max_tokens,
                  messages=[{"role": "system", "content": system},
                            {"role": "user", "content": user}])
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        r = client.chat.completions.create(**kw)
        u = r.usage
        return LLMResult(r.choices[0].message.content, u.prompt_tokens, u.completion_tokens)

    def _anthropic(self, system, user, model, temperature):
        import anthropic
        client = anthropic.Anthropic()
        r = client.messages.create(model=model, system=system, temperature=temperature,
                                    max_tokens=self.s.llm_max_tokens,
                                    messages=[{"role": "user", "content": user}])
        return LLMResult(r.content[0].text, r.usage.input_tokens, r.usage.output_tokens)

    def _ollama(self, system, user, model, temperature, json_mode):
        import requests
        payload = {"model": model, "stream": False,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "options": {"temperature": temperature}}
        if json_mode:
            payload["format"] = "json"
        r = requests.post(f"{self.s.ollama_host}/api/chat", json=payload, timeout=120)
        txt = r.json()["message"]["content"]
        return LLMResult(txt, len(user) // 4, len(txt) // 4)

    def _test(self, system, user) -> LLMResult:
        note = user.split("Customer note:")[-1]
        low = note.lower()
        sentiment = ("negative" if any(w in low for w in NEG)
                     else "positive" if any(w in low for w in ("love", "lovely", "great", "thanks", "nice"))
                     else "neutral")
        urgency = ("high" if any(w in low for w in URGENT)
                   else "low" if sentiment == "positive" else "medium")
        # redact PII so the summary never echoes secrets
        clean = CARD.sub("[card]", EMAIL.sub("[email]", note)).strip()
        out = {
            "summary": f"Customer note: {clean[:90]}",
            "sentiment": sentiment,
            "next_action": "escalate" if urgency == "high" else "follow up",
            "urgency": urgency,
            "confidence": 0.8,
        }
        text = json.dumps(out)
        return LLMResult(text, len(user) // 4, len(text) // 4)


def get_llm() -> LLMClient:
    return LLMClient()
