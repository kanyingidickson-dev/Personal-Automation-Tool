from __future__ import annotations

from pathlib import Path


def delete_empty_dirs(root: Path, *, protected: set[Path] | None = None) -> None:
    if not root.exists() or not root.is_dir():
        return

    protected = protected or set()

    for p in sorted(root.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if not p.is_dir() or p == root:
            continue

        if p in protected:
            continue

        if any(parent in protected for parent in p.parents):
            continue

        try:
            next(p.iterdir())
        except StopIteration:
            p.rmdir()
