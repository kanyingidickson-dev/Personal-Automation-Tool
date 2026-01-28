from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Rule:
    name: str
    extensions: list[str]
    destination: str


@dataclass(frozen=True)
class Config:
    source_dir: Path
    destinations: dict[str, str]
    rules: list[Rule]


def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping")

    source_dir = Path(str(data.get("source_dir", ".")))

    destinations_raw = data.get("destinations")
    if not isinstance(destinations_raw, dict):
        raise ValueError("destinations must be a mapping")

    destinations: dict[str, str] = {str(k): str(v) for k, v in destinations_raw.items()}

    rules_raw = data.get("rules")
    if not isinstance(rules_raw, list):
        raise ValueError("rules must be a list")

    rules: list[Rule] = []
    for r in rules_raw:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name"))
        destination = str(r.get("destination"))
        exts_raw = r.get("extensions")
        if not isinstance(exts_raw, list):
            exts_raw = []
        exts = [str(e) for e in exts_raw]
        rules.append(Rule(name=name, extensions=exts, destination=destination))

    return Config(source_dir=source_dir, destinations=destinations, rules=rules)
