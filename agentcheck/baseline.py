from __future__ import annotations

from pathlib import Path

from .storage import BASELINE_DIR, read_json, write_json


BASELINE_FILE = BASELINE_DIR / "latest.json"


def save_baseline(session_data: dict) -> Path:
    write_json(BASELINE_FILE, session_data)
    return BASELINE_FILE


def load_baseline() -> dict | None:
    if not BASELINE_FILE.exists():
        return None
    return read_json(BASELINE_FILE)
