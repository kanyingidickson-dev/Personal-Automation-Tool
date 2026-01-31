from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


@dataclass(frozen=True)
class Rule:
    name: str
    destination: str
    extensions: list[str]
    pattern: str | None
    regex: str | None
    priority: int
    duplicate_strategy: str


@dataclass(frozen=True)
class Config:
    source_dir: Path
    destinations: dict[str, str]
    rules: list[Rule]
    default_duplicate_strategy: str


def validate_config(cfg: Config) -> None:
    if not cfg.source_dir.exists() or not cfg.source_dir.is_dir():
        raise FileNotFoundError(f"source_dir not found or not a directory: {cfg.source_dir}")

    if not isinstance(cfg.destinations, dict):
        raise ValueError("destinations must be a mapping")

    if not cfg.default_duplicate_strategy:
        raise ValueError("default_duplicate_strategy must be set")

    valid_duplicate_strategies = {"skip", "rename", "overwrite"}
    if cfg.default_duplicate_strategy not in valid_duplicate_strategies:
        raise ValueError(
            "default_duplicate_strategy must be one of: skip, rename, overwrite"
        )

    for r in cfg.rules:
        if not r.destination:
            raise ValueError("rule.destination is required")

        if r.destination != "other" and r.destination not in cfg.destinations:
            raise ValueError(
                f"rule.destination must reference a key in destinations (got {r.destination})"
            )

        has_match = bool(r.extensions) or (r.pattern is not None) or (r.regex is not None)
        if not has_match:
            raise ValueError(
                "Each rule must provide at least one matcher: extensions, pattern, or regex"
            )

        for e in r.extensions:
            if not e.startswith("."):
                raise ValueError(
                    f"Rule extensions must start with '.' (got {e} in rule {r.name})"
                )

        if not isinstance(r.priority, int):
            raise ValueError("rule.priority must be an int")
        if r.duplicate_strategy not in valid_duplicate_strategies:
            raise ValueError(
                f"rule.duplicate_strategy must be one of: skip, rename, overwrite (got {r.duplicate_strategy})"
            )
        if r.regex is not None:
            re.compile(r.regex)


def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping")

    source_dir_raw = data.get("source_dir", ".")
    source_dir = Path(str(source_dir_raw)).expanduser()
    if not source_dir.is_absolute():
        source_dir = (path.parent / source_dir).resolve()

    destinations_raw = data.get("destinations")
    if destinations_raw is None:
        destinations_raw = {"other": "Other"}
    if not isinstance(destinations_raw, dict):
        raise ValueError("destinations must be a mapping")

    destinations: dict[str, str] = {str(k): str(v) for k, v in destinations_raw.items()}
    if "other" not in destinations:
        destinations["other"] = "Other"

    default_duplicate_strategy = str(data.get("duplicate_strategy", "skip"))

    rules_raw = data.get("rules")
    if rules_raw is None:
        rules_raw = []
    if not isinstance(rules_raw, list):
        raise ValueError("rules must be a list")

    rules: list[Rule] = []
    for r in rules_raw:
        if not isinstance(r, dict):
            continue

        destination = str(r.get("destination", ""))

        name_raw = r.get("name")
        if name_raw is None:
            name_raw = destination or "rule"
        name = str(name_raw)

        exts_raw = r.get("extensions")
        if not isinstance(exts_raw, list):
            exts_raw = []
        exts = [str(e) for e in exts_raw]

        pattern_raw = r.get("pattern")
        pattern = None if pattern_raw is None else str(pattern_raw)

        regex_raw = r.get("regex")
        regex = None if regex_raw is None else str(regex_raw)

        priority_raw = r.get("priority", 0)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid priority for rule {name}: {priority_raw}") from None

        duplicate_strategy_raw = r.get("duplicate_strategy", default_duplicate_strategy)
        duplicate_strategy = str(duplicate_strategy_raw)

        rules.append(
            Rule(
                name=name,
                destination=destination,
                extensions=exts,
                pattern=pattern,
                regex=regex,
                priority=priority,
                duplicate_strategy=duplicate_strategy,
            )
        )

    cfg = Config(
        source_dir=source_dir,
        destinations=destinations,
        rules=rules,
        default_duplicate_strategy=default_duplicate_strategy,
    )
    validate_config(cfg)
    return cfg
