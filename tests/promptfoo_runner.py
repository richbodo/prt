from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

COMMANDS = [
    ["promptfoo", "eval"],
    ["npx", "-y", "promptfoo", "eval"],
]


def run_promptfoo_scenario(path: Path) -> dict:
    """Run a promptfoo evaluation scenario and return JSON results."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = Path(tmp.name)

    try:
        for base in COMMANDS:
            try:
                subprocess.run(base + ["-c", str(path), "-o", str(output_path)], check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            raise RuntimeError("promptfoo CLI is not available")

        with output_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    finally:
        if output_path.exists():
            output_path.unlink()
