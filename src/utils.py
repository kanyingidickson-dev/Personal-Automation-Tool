from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.config_loader import Config


@dataclass(frozen=True)
class MoveAction:
    src: Path
    dst: Path
    rule_name: str


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def decide_destination(file_path: Path, cfg: Config) -> tuple[str, str]:
    ext = file_path.suffix.lower()

    for rule in cfg.rules:
        if ext in {e.lower() for e in rule.extensions}:
            return rule.destination, rule.name

    return "other", "fallback"


def plan_moves(cfg: Config) -> list[MoveAction]:
    source = cfg.source_dir
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"source_dir not found or not a directory: {source}")

    actions: list[MoveAction] = []

    for p in source.iterdir():
        if not p.is_file():
            continue

        dest_key, rule_name = decide_destination(p, cfg)
        dest_folder_name = cfg.destinations.get(dest_key, cfg.destinations.get("other", "Other"))
        dst_dir = source / dest_folder_name
        dst = dst_dir / p.name

        actions.append(MoveAction(src=p, dst=dst, rule_name=rule_name))

    return actions


def execute_moves(actions: list[MoveAction], *, dry_run: bool) -> None:
    for a in actions:
        a.dst.parent.mkdir(parents=True, exist_ok=True)

        logging.info("rule=%s src=%s dst=%s", a.rule_name, a.src, a.dst)
        if dry_run:
            continue

        shutil.move(str(a.src), str(a.dst))
