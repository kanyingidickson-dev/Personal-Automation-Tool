from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from src.config.config_loader import Config, Rule


def sorted_rules(cfg: Config) -> list[Rule]:
    return sorted(cfg.rules, key=lambda r: r.priority, reverse=True)


def rule_matches_file(rule: Rule, file_path: Path) -> bool:
    name = file_path.name

    if rule.regex:
        return re.match(rule.regex, name) is not None

    if rule.pattern:
        return fnmatch.fnmatch(name, rule.pattern)

    ext = file_path.suffix.lower()
    rule_exts = {e.lower() for e in rule.extensions}
    return ext in rule_exts


def select_rule(file_path: Path, cfg: Config) -> Rule | None:
    for rule in sorted_rules(cfg):
        if rule_matches_file(rule, file_path):
            return rule
    return None


def resolve_destination_folder(rule: Rule | None, cfg: Config) -> tuple[str, str]:
    if rule is None:
        dest_key = "other"
        rule_name = "fallback"
    else:
        dest_key = rule.destination
        rule_name = rule.name

    folder_name = cfg.destinations.get(dest_key)
    if folder_name is None:
        folder_name = dest_key or cfg.destinations.get("other", "Other")

    return folder_name, rule_name
