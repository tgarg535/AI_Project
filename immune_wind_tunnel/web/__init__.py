"""Flask HTTP layer for the Immune Wind Tunnel."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from immune_wind_tunnel.agent import propose_action
from immune_wind_tunnel.config import SCORECARD_PATH
from immune_wind_tunnel.immune import check_action, check_input
from immune_wind_tunnel.tools import execute_tool
from immune_wind_tunnel.wind_tunnel import QUARANTINE_BANNER, run_wind_tunnel

_last_results: list[dict] = []


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
    )

    @app.get("/")
    def home():
        return render_template("index.html", results=_last_results)

    @app.get("/live")
    def live():
        """Separate page: type a prompt and see the two-checkpoint result."""
        return render_template("live.html")

    @app.post("/api/run")
    def api_run():
        global _last_results
        _last_results = run_wind_tunnel()
        return jsonify(
            {
                "ok": True,
                "results": _last_results,
                "artifact": SCORECARD_PATH.name,
            }
        )

    @app.get("/scorecard")
    def scorecard():
        if not SCORECARD_PATH.exists():
            return "Run the wind tunnel first.", 404
        return SCORECARD_PATH.read_text(encoding="utf-8"), 200, {
            "Content-Type": "text/markdown; charset=utf-8"
        }

    @app.post("/api/check")
    def api_check():
        """Run the full two-checkpoint pipeline on a single prompt."""
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"error": "text required"}), 400

        input_verdict, input_backend = check_input(text)
        if input_verdict == "QUARANTINE":
            print(QUARANTINE_BANNER)
            return jsonify(
                {
                    "input_verdict": input_verdict,
                    "input_backend": input_backend,
                    "proposed": None,
                    "action_verdict": None,
                    "verdict": "QUARANTINE",
                    "blocked_at": "input",
                    "tool_executed": False,
                    "tool_executed_label": "No",
                    "result": "BLOCKED",
                    "outcome": "Execution Halted & Frozen (input gate)",
                }
            )

        decision = propose_action(text)
        action_verdict, action_backend = check_action(
            decision["action"], decision["arguments"]
        )
        if action_verdict == "QUARANTINE":
            print(QUARANTINE_BANNER)
            return jsonify(
                {
                    "input_verdict": input_verdict,
                    "input_backend": input_backend,
                    "proposed": decision,
                    "action_verdict": action_verdict,
                    "action_backend": action_backend,
                    "verdict": "QUARANTINE",
                    "blocked_at": "action",
                    "tool_executed": False,
                    "tool_executed_label": "No",
                    "result": "CONTAINED",
                    "outcome": "Execution Halted & Frozen (action gate)",
                }
            )

        tool_result = execute_tool(decision["action"], decision["arguments"])
        return jsonify(
            {
                "input_verdict": input_verdict,
                "input_backend": input_backend,
                "proposed": decision,
                "action_verdict": action_verdict,
                "action_backend": action_backend,
                "verdict": "ALLOW",
                "blocked_at": "none",
                "tool_executed": True,
                "tool_executed_label": "Yes",
                "result": "PASS",
                "outcome": tool_result,
            }
        )

    return app
