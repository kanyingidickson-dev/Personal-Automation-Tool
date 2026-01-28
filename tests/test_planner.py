from pathlib import Path

from src.config_loader import load_config
from src.utils import plan_moves


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
