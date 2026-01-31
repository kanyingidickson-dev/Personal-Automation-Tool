# Personal Automation Tool

![CI](https://github.com/kanyingidickson-dev/Personal-Automation-Tool/actions/workflows/ci.yml/badge.svg)

A small, useful automation utility that organizes files in a folder according to configurable rules.

This repo is designed to be:
- practical (solves a real repetitive task)
- safe (supports dry-run)
- schedulable (cron-ready)
- configurable (YAML config)

## Problem statement

Downloads/Desktop folders tend to accumulate files. Manually sorting them is repetitive and easy to forget.

This tool automatically moves files into destination subfolders based on rules (extensions, filename patterns), and logs what happened.

## Tech stack

- Python
- PyYAML

## Folder structure

- `src/` application code
- `config/` YAML configuration
- `logs/` runtime logs (gitignored)

## How to run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m src.main --config config/rules.yaml --dry-run
python -m src.main --config config/rules.yaml
```

## CLI options

```bash
# log configuration
python -m src.main --config config/rules.yaml --log-level DEBUG --log-file ./logs/output.log

# delete empty directories after moves
python -m src.main --config config/rules.yaml --delete-empty-dirs

# record moves to a ledger file (used for undo)
python -m src.main --config config/rules.yaml --ledger-file ./logs/move_ledger.jsonl

# undo the last recorded move
python -m src.main --undo-last --ledger-file ./logs/move_ledger.jsonl
```

## Example configuration

See `config/rules.yaml`.

## Scheduling (cron)

Example (run every day at 6pm):

```cron
0 18 * * * /usr/bin/python3 -m src.main --config /path/to/automation-tool/config/rules.yaml --ledger-file /path/to/automation-tool/logs/move_ledger.jsonl >> /path/to/automation-tool/logs/cron.log 2>&1
```

## Design decisions

- A **dry-run** mode is the default recommended mode for first runs.
- Moves are performed using `pathlib` and `shutil.move` for portability.
- Logs are written to `logs/automation.log`.

## Rule configuration features

Rules can match files using any of:

- `extensions` (e.g. `['.pdf', '.png']`)
- `pattern` (fnmatch/glob style, e.g. `"report_*.pdf"`)
- `regex` (Python regex matched against the filename)

If multiple rules match, the rule with the highest `priority` wins.

Duplicate handling is controlled by:

- global `duplicate_strategy`: `skip` (default), `rename`, `overwrite`
- optional per-rule `duplicate_strategy`

## Web UI demo (optional)

If you want a simple browser-based interface (dry-run, execute, undo), you can run the Streamlit demo app.

```bash
pip install -r requirements-ui.txt
streamlit run streamlit_app.py
```

## GitHub Pages (static site)

This repository includes a static landing page under `docs/` that can be deployed with GitHub Pages.

Important:

- GitHub Pages can only host **static** files (HTML/CSS/JS).
- The interactive GUI is the **Streamlit** app (`streamlit_app.py`), which must be run locally or deployed to a Python-capable host.

To enable Pages for this repo:

- Go to **Settings** -> **Pages**
- Under **Build and deployment**, set **Source** to **GitHub Actions**

After you merge to `main`, the workflow `.github/workflows/pages.yml` deploys `docs/` to:

- `https://kanyingidickson-dev.github.io/Personal-Automation-Tool/`

## Future improvements

- Add richer rule conditions (size/date ranges, nested destination paths)
- Add notifications (email/Slack) for success/failures
- Add packaging for distribution (PyPI)
