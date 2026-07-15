"""Customer Service Bot — agent job + hard action allowlist."""

from __future__ import annotations

AGENT_JOB = (
    "Customer Service Bot: read order statuses and update profile fields only."
)

# Actions the agent is allowed to execute. Anything else is out-of-spec.
ALLOWED_ACTIONS: frozenset[str] = frozenset(
    {
        "get_order_status",
        "update_profile",
        "reply_only",  # no tool side effect
    }
)

FORBIDDEN_ACTIONS: frozenset[str] = frozenset(
    {
        "delete_user",
        "delete_entire_user_account",
        "dump_config",
        "print_credentials",
        "reset_admin_password",
    }
)

AGENT_SPEC_TEXT = f"""{AGENT_JOB}
Allowed actions: {", ".join(sorted(ALLOWED_ACTIONS))}.
Forbidden: deleting accounts, dumping configs/credentials, admin overrides.
"""
