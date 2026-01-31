from pathlib import Path

from src.automation.undo_manager import undo_last_move
from src.config_loader import load_config
from src.utils import delete_empty_dirs, execute_moves, plan_moves


def test_plan_moves_routes_extensions(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "a.pdf").write_text("x", encoding="utf-8")
    (inbox / "b.png").write_text("x", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}

destinations:
  documents: Documents
  images: Images
  other: Other

rules:
  - name: documents
    extensions: ['.pdf']
    destination: documents
  - name: images
    extensions: ['.png']
    destination: images
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)

    assert len(actions) == 2
    dsts = {a.src.name: a.dst.parent.name for a in actions}
    assert dsts["a.pdf"] == "Documents"
    assert dsts["b.png"] == "Images"


def test_rule_priority_wins_when_multiple_rules_match(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "special.txt").write_text("x", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}

destinations:
  high: High
  low: Low
  other: Other

rules:
  - name: low
    extensions: ['.txt']
    destination: low
    priority: 0
  - name: high
    regex: '^special\\.txt$'
    destination: high
    priority: 10
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)

    assert len(actions) == 1
    assert actions[0].dst.parent.name == "High"


def test_regex_rule_routes_file(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "pic_2022.jpg").write_text("x", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}

destinations:
  y2022: Y2022
  other: Other

rules:
  - name: y2022
    regex: '.*_2022.*\\.jpg$'
    destination: y2022
    priority: 0
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)

    assert len(actions) == 1
    assert actions[0].dst.parent.name == "Y2022"


def test_duplicate_strategy_skip(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "a.txt").write_text("new", encoding="utf-8")
    (inbox / "Docs").mkdir()
    (inbox / "Docs" / "a.txt").write_text("old", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}
duplicate_strategy: skip

destinations:
  docs: Docs
  other: Other

rules:
  - name: docs
    extensions: ['.txt']
    destination: docs
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)
    execute_moves(actions, dry_run=False)

    assert (inbox / "a.txt").exists()
    assert (inbox / "Docs" / "a.txt").read_text(encoding="utf-8") == "old"


def test_duplicate_strategy_overwrite(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "a.txt").write_text("new", encoding="utf-8")
    (inbox / "Docs").mkdir()
    (inbox / "Docs" / "a.txt").write_text("old", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}
duplicate_strategy: overwrite

destinations:
  docs: Docs
  other: Other

rules:
  - name: docs
    extensions: ['.txt']
    destination: docs
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)
    execute_moves(actions, dry_run=False)

    assert not (inbox / "a.txt").exists()
    assert (inbox / "Docs" / "a.txt").read_text(encoding="utf-8") == "new"


def test_duplicate_strategy_rename(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "a.txt").write_text("new", encoding="utf-8")
    (inbox / "Docs").mkdir()
    (inbox / "Docs" / "a.txt").write_text("old", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}
duplicate_strategy: rename

destinations:
  docs: Docs
  other: Other

rules:
  - name: docs
    extensions: ['.txt']
    destination: docs
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)
    execute_moves(actions, dry_run=False)

    assert not (inbox / "a.txt").exists()
    assert (inbox / "Docs" / "a.txt").read_text(encoding="utf-8") == "old"
    renamed = [p for p in (inbox / "Docs").iterdir() if p.name != "a.txt"]
    assert len(renamed) == 1
    assert renamed[0].suffix == ".txt"


def test_delete_empty_dirs_preserves_protected_destination_folders(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    docs = inbox / "Docs"
    docs.mkdir()

    empty_nested = inbox / "empty" / "nested"
    empty_nested.mkdir(parents=True)

    delete_empty_dirs(inbox, protected={docs})

    assert docs.exists()
    assert not (inbox / "empty").exists()


def test_undo_last_move_restores_file_from_ledger(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    (inbox / "a.txt").write_text("x", encoding="utf-8")

    cfg_path = tmp_path / "rules.yaml"
    cfg_path.write_text(
        """
source_dir: {src}

destinations:
  docs: Docs
  other: Other

rules:
  - name: docs
    extensions: ['.txt']
    destination: docs
""".format(src=str(inbox)),
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    actions = plan_moves(cfg)

    ledger = tmp_path / "ledger.jsonl"
    execute_moves(actions, dry_run=False, ledger_path=ledger)

    assert not (inbox / "a.txt").exists()
    assert (inbox / "Docs" / "a.txt").exists()
    assert ledger.exists()

    restored_to = undo_last_move(ledger)
    assert restored_to.exists()
