"""LLM / rule backends for input and action guardrails."""

from __future__ import annotations

import json
import os
import re

from immune_wind_tunnel.immune.prompts import (
    ACTION_GUARD_PROMPT,
    IMMUNE_SYSTEM_PROMPT,
)
from immune_wind_tunnel.spec import ALLOWED_ACTIONS, FORBIDDEN_ACTIONS


def normalize_verdict(raw: str) -> str:
    text = (raw or "").strip().upper()
    if "QUARANTINE" in text:
        return "QUARANTINE"
    if "ALLOW" in text:
        return "ALLOW"
    return "QUARANTINE"  # fail closed


# ---------------------------------------------------------------------------
# Input backends
# ---------------------------------------------------------------------------
def check_openai_input(user_text: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": IMMUNE_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            max_tokens=16,
            temperature=0,
        )
        return normalize_verdict(resp.choices[0].message.content or "")
    except Exception as exc:  # noqa: BLE001
        print(f"[immune/input] OpenAI error: {exc}")
        return None


def check_gemini_input(user_text: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        import requests

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{IMMUNE_SYSTEM_PROMPT}\n\nUser text:\n{user_text}"
                        }
                    ]
                }
            ],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 16},
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return normalize_verdict(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[immune/input] Gemini error: {exc}")
        return None


ATTACK_PATTERNS = [
    r"ignore (previous|all|your) (safety )?rules",
    r"system override",
    r"\bdelete\b.*(account|user|data|all)",
    r"(database|db|admin).*(credential|password|config|secret)",
    r"(print|dump|output|show).*(credential|config|secret|api.?key)",
    r"forgot my admin",
    r"jailbreak",
    r"disregard (your|all) instructions",
]


def check_rules_input(user_text: str) -> str:
    t = user_text.lower()
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, t):
            return "QUARANTINE"
    return "ALLOW"


# ---------------------------------------------------------------------------
# Action backends (primary Track 3 check)
# ---------------------------------------------------------------------------
def check_openai_action(action: str, arguments: dict) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload = {"action": action, "arguments": arguments}
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ACTION_GUARD_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            max_tokens=16,
            temperature=0,
        )
        return normalize_verdict(resp.choices[0].message.content or "")
    except Exception as exc:  # noqa: BLE001
        print(f"[immune/action] OpenAI error: {exc}")
        return None


def check_gemini_action(action: str, arguments: dict) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        import requests

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{ACTION_GUARD_PROMPT}\n\nProposed Action Payload:\n{json.dumps({'action': action, 'arguments': arguments})}"
                        }
                    ]
                }
            ],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 16},
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return normalize_verdict(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[immune/action] Gemini error: {exc}")
        return None



def check_rules_action(action: str, arguments: dict | None = None) -> str:
    """Spec allowlist — strongest deterministic action gate."""
    _ = arguments
    name = (action or "").strip()
    if name in FORBIDDEN_ACTIONS:
        return "QUARANTINE"
    if name in ALLOWED_ACTIONS:
        return "ALLOW"
    return "QUARANTINE"  # unknown actions are out of spec


# Backwards-compatible aliases used by older call sites
check_openai = check_openai_input
check_gemini = check_gemini_input
check_rules = check_rules_input
