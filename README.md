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
pip install -r requirements.txt
python -m src.main --config config/rules.yaml --dry-run
python -m src.main --config config/rules.yaml
```

## Example configuration

See `config/rules.yaml`.

## Scheduling (cron)

Example (run every day at 6pm):

```cron
0 18 * * * /usr/bin/python3 /path/to/automation-tool/src/main.py --config /path/to/automation-tool/config/rules.yaml >> /path/to/automation-tool/logs/cron.log 2>&1
```

## Design decisions

- A **dry-run** mode is the default recommended mode for first runs.
- Moves are performed using `pathlib` and `shutil.move` for portability.
- Logs are written to `logs/automation.log`.

## Future improvements

- Add duplicate-handling strategy (rename/skip/overwrite)
- Add rule priority and regex rules
- Add unit tests for more edge cases
- Add `--delete-empty-dirs` option
