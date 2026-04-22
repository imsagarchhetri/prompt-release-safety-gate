"""Pydantic schemas: the AI feature's output contract + prompt config.

A prompt that returns beautiful prose but breaks this schema fails the gate.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class CRMSummary(BaseModel):
    summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    next_action: str
    urgency: Literal["low", "medium", "high"]
    confidence: float

    @field_validator("confidence")
    @classmethod
    def _conf_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        return v


class PromptConfig(BaseModel):
    version: str
    owner: str = "unknown"
    description: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    system_prompt: str


# Public price table (USD / 1M tokens) for cost accounting in the gate.
PRICES = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
    "claude-haiku": (0.80, 4.0),
    "claude-sonnet": (3.0, 15.0),
    "llama3.1": (0.0, 0.0),
}


def cost_usd(model: str, in_tok: int, out_tok: int) -> float:
    pin, pout = PRICES.get(model, (0.15, 0.60))
    return in_tok / 1e6 * pin + out_tok / 1e6 * pout
