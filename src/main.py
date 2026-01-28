from __future__ import annotations

import argparse
from pathlib import Path

from src.config_loader import load_config
from src.utils import execute_moves, plan_moves, setup_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Personal Automation Tool (file organizer)")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Log planned moves without moving files")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_config(config_path)

    setup_logging(Path("logs/automation.log"))

    actions = plan_moves(cfg)
    execute_moves(actions, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
