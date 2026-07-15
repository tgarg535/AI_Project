"""Shared paths and environment loading."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SCORECARD_PATH = ROOT / "quarantine_scorecard.md"
