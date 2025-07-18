# prt
Personal Relationship Toolkit is a privacy-first client-side encrypted database designed to support mental health through intentional relationship management.

Started ideating on this here: http://richbodo.pbworks.com/w/page/160555728/Personal%20Social%20Network%20Health

I had a few AIs convert those notes to PRDs, then synthesized an MVP PRD: [PRD/prt_prd_mvp.md](PRD/prt_prd_mvp.md) for the consolidated requirements.

## Setup

Run all commands from the repository root (the directory containing this README).

Create a virtual environment and install dependencies:

```bash
source ./init.sh
```

The script creates a `.venv` directory and installs packages listed in
`requirements.txt`.

## Running the CLI

The main application is a Typer CLI located inside the `prt` package. Launch it
with:

```bash
python -m prt.cli
```

Because the project folder shares the same name as the package, ensure you are
in the repository root before executing this command.

## Running the tests


```bash
pytest -q
```

## Exit the virtual environment

```bash
source ./uninit.sh
```


