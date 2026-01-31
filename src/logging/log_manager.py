from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_path: Path, *, level: str = "INFO") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f"Invalid log level: {level}")

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    console_handler = logging.StreamHandler()

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[file_handler, console_handler],
        force=True,
    )
