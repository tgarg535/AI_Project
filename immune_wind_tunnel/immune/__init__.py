"""Two-checkpoint Immune System: input guard + action guard."""

from __future__ import annotations

from typing import Any

from immune_wind_tunnel.immune.backends import (
    check_gemini_input,
    check_openai_action,
    check_openai_input,
    check_rules_action,
    check_rules_input,
)


def check_input(user_text: str) -> tuple[str, str]:
    """Checkpoint 1 — cheap filter on raw user text."""
    for checker, name in (
        (check_openai_input, "openai-input"),
        (check_gemini_input, "gemini-input"),
    ):
        verdict = checker(user_text)
        if verdict is not None:
            return verdict, name
    return check_rules_input(user_text), "rules-input"


def check_action(action: str, arguments: dict[str, Any] | None = None) -> tuple[str, str]:
    """
    Checkpoint 2 — Track 3 core: inspect proposed tool call before it fires.

    Prefer the deterministic allowlist; optionally consult an LLM for nuance.
    """
    arguments = arguments or {}
    # Spec allowlist is the source of truth for the demo (deterministic + explainable)
    rules_verdict = check_rules_action(action, arguments)

    # Optional LLM second opinion (does not override QUARANTINE from rules)
    llm = check_openai_action(action, arguments)
    if llm is not None and rules_verdict == "ALLOW" and llm == "QUARANTINE":
        return "QUARANTINE", "openai-action"
    return rules_verdict, "spec-allowlist"


# Backwards-compatible name → input checkpoint
def immune_system_check(user_text: str) -> tuple[str, str]:
    return check_input(user_text)


__all__ = [
    "check_action",
    "check_input",
    "immune_system_check",
]
