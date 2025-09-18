# Evaluation Datasets

The `tests/evals` directory contains small YAML datasets used to
exercise language-model behaviours that matter for PRT. Each file
contains a list of prompts alongside the expected behaviour of the
model.

## Running the datasets

Run an evaluation by supplying the YAML file to the evaluation harness:

```bash
python -m prt_src.evals.run tests/evals/sql_safety.yaml
python -m prt_src.evals.run tests/evals/contact_discovery.yaml
```

The command prints a score for each case and a summary at the end. A
higher score indicates better alignment with the expectations encoded in
the YAML file.

## Available datasets

### SQL safety

*File*: `tests/evals/sql_safety.yaml`

Prompts crafted to resemble SQL injection or destructive database
operations. The model should refuse to generate the requested SQL or
explain why the request is unsafe.

### Contact discovery

*File*: `tests/evals/contact_discovery.yaml`

Short passages that contain names, phone numbers, or email addresses. The
model is expected to identify and return the relevant contact
information.

## Interpreting results

- **Pass** – the model's response matches the `ideal` or `expected`
  value for the test case.
- **Fail** – the model's response diverges from what is specified in the
  YAML file. Review the model behaviour and adjust prompting or training
  as needed.

These datasets are intentionally small and serve as smoke tests. Extend
them with additional cases to cover more scenarios.
