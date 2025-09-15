import json
import shutil
from pathlib import Path

import pytest
from promptfoo_runner import run_promptfoo_scenario

EVAL_PATH = Path(__file__).parent / "evals" / "echo_basic.yaml"


def _promptfoo_available():
    """Check if promptfoo CLI is actually functional."""
    import subprocess

    # Check if promptfoo command exists and works
    if shutil.which("promptfoo"):
        try:
            subprocess.run(["promptfoo", "--version"], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check if npx promptfoo works (requires Node.js 20+)
    if shutil.which("npx"):
        try:
            subprocess.run(
                ["npx", "--yes", "promptfoo", "--version"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return False


# Skip all tests if promptfoo is not available or functional
pytestmark = pytest.mark.skipif(
    not _promptfoo_available(),
    reason="promptfoo CLI not available or functional (requires Node.js 20+)",
)


def test_promptfoo_runs_scenarios():
    result = run_promptfoo_scenario(EVAL_PATH)
    assert isinstance(result, dict)
    # ensure some results are present
    assert result


def test_promptfoo_output_contains_scores():
    result = run_promptfoo_scenario(EVAL_PATH)
    serialized = json.dumps(result).lower()
    assert "score" in serialized
