from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import shutil

from src.automation.rules_engine import resolve_destination_folder, select_rule
from src.automation.undo_manager import LedgerEntry, append_ledger_entry
from src.config.config_loader import Config


@dataclass(frozen=True)
class MoveAction:
    src: Path
    dst: Path
    rule_name: str
    duplicate_strategy: str


def plan_moves(cfg: Config) -> list[MoveAction]:
    source = cfg.source_dir
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"source_dir not found or not a directory: {source}")

    actions: list[MoveAction] = []

    for p in source.iterdir():
        if not p.is_file():
            continue

        rule = select_rule(p, cfg)
        dest_folder_name, rule_name = resolve_destination_folder(rule, cfg)
        duplicate_strategy = cfg.default_duplicate_strategy if rule is None else rule.duplicate_strategy

        dst_dir = source / dest_folder_name
        dst = dst_dir / p.name

        actions.append(
            MoveAction(
                src=p,
                dst=dst,
                rule_name=rule_name,
                duplicate_strategy=duplicate_strategy,
            )
        )

    return actions


def _unique_renamed_path(dst: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = dst.with_name(f"{dst.stem}_{stamp}{dst.suffix}")
    if not candidate.exists():
        return candidate

    i = 1
    while True:
        candidate = dst.with_name(f"{dst.stem}_{stamp}_{i}{dst.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def execute_moves(
    actions: list[MoveAction],
    *,
    dry_run: bool,
    ledger_path: Path | None = None,
) -> None:
    for a in actions:
        dst = a.dst
        src = a.src

        if dst.exists():
            if a.duplicate_strategy == "skip":
                logging.info(
                    "action=skip_duplicate rule=%s src=%s dst=%s",
                    a.rule_name,
                    a.src,
                    dst,
                )
                continue

            if a.duplicate_strategy == "rename":
                dst = _unique_renamed_path(dst)

            if a.duplicate_strategy == "overwrite":
                if not dry_run and dst.exists():
                    dst.unlink()

        dst.parent.mkdir(parents=True, exist_ok=True)

        logging.info(
            "action=move rule=%s src=%s dst=%s duplicate_strategy=%s",
            a.rule_name,
            a.src,
            dst,
            a.duplicate_strategy,
        )
        if dry_run:
            continue

        shutil.move(str(src), str(dst))

        if ledger_path is not None:
            append_ledger_entry(
                ledger_path,
                LedgerEntry(
                    src=str(src),
                    dst=str(dst),
                    ts=datetime.now().isoformat(timespec="seconds"),
                    rule_name=a.rule_name,
                    duplicate_strategy=a.duplicate_strategy,
                ),
            )
