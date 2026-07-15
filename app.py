"""
Entrypoint for the Agent Immune Wind Tunnel.

  python app.py --run   # terminal binary demo + scorecard
  python app.py         # Flask UI on :5000
"""

from __future__ import annotations

import os
import sys

from immune_wind_tunnel.web import create_app
from immune_wind_tunnel.wind_tunnel import run_wind_tunnel


def _force_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> None:
    _force_utf8()

    if "--run" in sys.argv:
        run_wind_tunnel()
        return

    app = create_app()
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"Immune Wind Tunnel → http://127.0.0.1:{port}")
    print("Tip: python app.py --run   # terminal-only binary demo")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
