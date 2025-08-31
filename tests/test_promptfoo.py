import json
from pathlib import Path

from promptfoo_runner import run_promptfoo_scenario

EVAL_PATH = Path(__file__).parent / "evals" / "echo_basic.yaml"


def test_promptfoo_runs_scenarios():
    result = run_promptfoo_scenario(EVAL_PATH)
    assert isinstance(result, dict)
    # ensure some results are present
    assert result


def test_promptfoo_output_contains_scores():
    result = run_promptfoo_scenario(EVAL_PATH)
    serialized = json.dumps(result).lower()
    assert "score" in serialized
