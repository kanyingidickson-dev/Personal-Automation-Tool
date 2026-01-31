from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LedgerEntry:
    src: str
    dst: str
    ts: str
    rule_name: str
    duplicate_strategy: str


def append_ledger_entry(ledger_path: Path, entry: LedgerEntry) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.__dict__, sort_keys=True) + "\n")


def _read_last_nonempty_line(path: Path) -> str | None:
    if not path.exists():
        return None

    with path.open("rb") as f:
        f.seek(0, 2)
        end = f.tell()
        if end == 0:
            return None

        buf = b""
        pos = end
        while pos > 0:
            step = min(4096, pos)
            pos -= step
            f.seek(pos)
            buf = f.read(step) + buf
            if b"\n" in buf:
                break

    lines = buf.splitlines()
    for raw in reversed(lines):
        line = raw.decode("utf-8").strip()
        if line:
            return line
    return None


def undo_last_move(ledger_path: Path) -> Path:
    line = _read_last_nonempty_line(ledger_path)
    if line is None:
        raise FileNotFoundError(f"No undo information found at: {ledger_path}")

    payload = json.loads(line)
    src = Path(payload["src"])
    dst = Path(payload["dst"])

    if not dst.exists():
        raise FileNotFoundError(f"Cannot undo because destination file is missing: {dst}")

    target_src = src
    if target_src.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_src = src.with_name(f"{src.stem}_undo_{stamp}{src.suffix}")

    target_src.parent.mkdir(parents=True, exist_ok=True)
    dst.replace(target_src)

    return target_src
