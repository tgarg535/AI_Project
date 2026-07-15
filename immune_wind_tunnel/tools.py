"""Mock tools — only called after the action guardrail ALLOWs."""

from __future__ import annotations

from typing import Any


def execute_tool(action: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Simulate side effects. Never call this before immune clearance."""
    if action == "get_order_status":
        oid = arguments.get("order_id", "?")
        return {
            "ok": True,
            "tool": action,
            "result": f"Order #{oid} shipped via UPS, ETA tomorrow.",
        }
    if action == "update_profile":
        field = arguments.get("field", "unknown")
        return {
            "ok": True,
            "tool": action,
            "result": f"Profile field '{field}' updated.",
        }
    if action == "reply_only":
        return {"ok": True, "tool": action, "result": "No side-effect reply sent."}

    # Should never reach here if the immune system is doing its job
    return {
        "ok": False,
        "tool": action,
        "result": f"REFUSED: tool '{action}' must not execute (guardrail gap).",
    }
