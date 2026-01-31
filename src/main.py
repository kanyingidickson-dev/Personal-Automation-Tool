from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.automation.undo_manager import undo_last_move
from src.config_loader import load_config
from src.utils import delete_empty_dirs, execute_moves, plan_moves, setup_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Personal Automation Tool (file organizer)")
    parser.add_argument("--config", help="Path to YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Log planned moves without moving files")
    parser.add_argument(
        "--delete-empty-dirs",
        action="store_true",
        help="Delete empty directories under source_dir after moves",
    )
    parser.add_argument(
        "--ledger-file",
        default="logs/move_ledger.jsonl",
        help="Path to actions ledger used for undo (default: logs/move_ledger.jsonl)",
    )
    parser.add_argument(
        "--undo-last",
        action="store_true",
        help="Undo the last recorded move from the ledger file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--log-file",
        default="logs/automation.log",
        help="Path to log file (default: logs/automation.log)",
    )
    args = parser.parse_args()

    setup_logging(Path(args.log_file), level=args.log_level)

    ledger_path = Path(args.ledger_file)

    if args.undo_last:
        restored_to = undo_last_move(ledger_path)
        logging.info("action=undo restored_to=%s", restored_to)
        return 0

    if not args.config:
        parser.error("--config is required unless --undo-last is provided")

    config_path = Path(args.config)
    cfg = load_config(config_path)

    actions = plan_moves(cfg)
    execute_moves(
        actions,
        dry_run=args.dry_run,
        ledger_path=None if args.dry_run else ledger_path,
    )

    if args.delete_empty_dirs and not args.dry_run:
        protected = {cfg.source_dir / name for name in cfg.destinations.values()}
        delete_empty_dirs(cfg.source_dir, protected=protected)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
