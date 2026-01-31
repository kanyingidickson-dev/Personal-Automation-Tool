from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.automation.undo_manager import undo_last_move
from src.config_loader import load_config
from src.utils import delete_empty_dirs, execute_moves, plan_moves


def _load_config_from_ui() -> Path:
    st.subheader("Configuration")

    config_path = st.text_input("Config path", value="config/rules.yaml")
    uploaded = st.file_uploader("Or upload a YAML config", type=["yaml", "yml"])

    if uploaded is not None:
        tmp = tempfile.NamedTemporaryFile(prefix="automation_cfg_", suffix=".yaml", delete=False)
        tmp.write(uploaded.getvalue())
        tmp.flush()
        return Path(tmp.name)

    return Path(config_path)


def main() -> None:
    st.set_page_config(page_title="Personal Automation Tool", layout="wide")
    st.title("Personal Automation Tool")

    cfg_path = _load_config_from_ui()

    st.subheader("Run options")
    dry_run = st.checkbox("Dry run", value=True)
    delete_empty = st.checkbox("Delete empty directories after moves", value=False)

    ledger_file = Path(st.text_input("Ledger file", value="logs/move_ledger.jsonl"))

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Plan", type="primary"):
            try:
                cfg = load_config(cfg_path)
                actions = plan_moves(cfg)
                st.session_state["_cfg"] = cfg
                st.session_state["_actions"] = actions
                st.success(f"Planned {len(actions)} file actions")
            except Exception as e:
                st.error(str(e))

    with col_b:
        if st.button("Undo last move"):
            try:
                restored_to = undo_last_move(ledger_file)
                st.success(f"Restored to: {restored_to}")
            except Exception as e:
                st.error(str(e))

    actions = st.session_state.get("_actions")
    cfg = st.session_state.get("_cfg")

    if actions:
        st.subheader("Planned actions")
        rows = [
            {
                "src": str(a.src),
                "dst": str(a.dst),
                "rule": a.rule_name,
                "duplicate_strategy": a.duplicate_strategy,
            }
            for a in actions
        ]
        st.dataframe(rows, use_container_width=True)

        confirm = st.checkbox("I understand this may move files", value=False, disabled=dry_run)
        run_disabled = (not dry_run) and (not confirm)

        if st.button("Execute", disabled=run_disabled):
            if cfg is None:
                st.error("Please click Plan first")
                return

            try:
                execute_moves(
                    actions,
                    dry_run=dry_run,
                    ledger_path=None if dry_run else ledger_file,
                )

                if delete_empty and not dry_run:
                    protected = {cfg.source_dir / name for name in cfg.destinations.values()}
                    delete_empty_dirs(cfg.source_dir, protected=protected)

                st.success("Done")
            except Exception as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
