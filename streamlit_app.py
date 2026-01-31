from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.automation.undo_manager import undo_last_move
from src.config_loader import load_config
from src.utils import delete_empty_dirs, execute_moves, plan_moves


THEME_TOKENS = {
    "dark": {
        "bg": "#0f1115",
        "bg_gradient": (
            "radial-gradient(circle at 12% 18%, rgba(74, 144, 226, 0.18), transparent 46%), "
            "linear-gradient(135deg, #0f1115 0%, #141924 55%, #0f1115 100%)"
        ),
        "sidebar_bg": "#11141a",
        "card_bg": "#171c24",
        "card_border": "#2a303b",
        "text": "#f3f5f7",
        "muted": "#a4adba",
        "accent": "#4A90E2",
        "accent_soft": "rgba(74, 144, 226, 0.16)",
        "input_bg": "#121821",
        "shadow": "0 20px 50px rgba(0, 0, 0, 0.35)",
        "shadow_soft": "0 12px 28px rgba(0, 0, 0, 0.25)",
    },
    "light": {
        "bg": "#f5f6f8",
        "bg_gradient": (
            "radial-gradient(circle at 8% 12%, rgba(74, 144, 226, 0.16), transparent 45%), "
            "linear-gradient(135deg, #f7f8fa 0%, #eef1f6 100%)"
        ),
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "card_border": "#dde2ea",
        "text": "#1f2430",
        "muted": "#5c6672",
        "accent": "#4A90E2",
        "accent_soft": "rgba(74, 144, 226, 0.12)",
        "input_bg": "#f4f6f9",
        "shadow": "0 20px 45px rgba(15, 23, 42, 0.12)",
        "shadow_soft": "0 12px 24px rgba(15, 23, 42, 0.08)",
    },
}


def _apply_theme(theme: str) -> None:
    tokens = THEME_TOKENS[theme]
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

        :root {{
            --bg: {tokens["bg"]};
            --bg-gradient: {tokens["bg_gradient"]};
            --sidebar-bg: {tokens["sidebar_bg"]};
            --card-bg: {tokens["card_bg"]};
            --card-border: {tokens["card_border"]};
            --text: {tokens["text"]};
            --muted: {tokens["muted"]};
            --accent: {tokens["accent"]};
            --accent-soft: {tokens["accent_soft"]};
            --input-bg: {tokens["input_bg"]};
            --shadow: {tokens["shadow"]};
            --shadow-soft: {tokens["shadow_soft"]};
            --font-sans: 'Space Grotesk', sans-serif;
            --font-mono: 'DM Mono', monospace;
        }}

        html, body, [class*="css"] {{
            font-family: var(--font-sans);
            color: var(--text);
        }}

        .stApp {{
            background: var(--bg-gradient);
            color: var(--text);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: var(--sidebar-bg);
            border-right: 1px solid var(--card-border);
        }}

        .block-container {{
            padding-top: 2.5rem;
            max-width: 1180px;
        }}

        h1, h2, h3, h4 {{
            letter-spacing: -0.02em;
        }}

        .hero {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 2rem 2.4rem;
            box-shadow: var(--shadow);
            animation: fadeIn 0.6s ease;
        }}

        .hero-eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.2em;
            font-size: 0.75rem;
            color: var(--muted);
            font-weight: 600;
            margin-bottom: 0.6rem;
        }}

        .hero-title {{
            font-size: 2.3rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }}

        .hero-subtitle {{
            font-size: 1rem;
            color: var(--muted);
            margin-bottom: 1.2rem;
        }}

        .hero-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }}

        .pill {{
            background: var(--accent-soft);
            color: var(--text);
            padding: 0.4rem 0.8rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        div[data-testid="stMetric"] {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 1.1rem 1.2rem;
            box-shadow: var(--shadow-soft);
        }}

        div[data-testid="stMetric"] label {{
            color: var(--muted) !important;
        }}

        .stButton > button {{
            background: var(--accent);
            color: #ffffff;
            border: 1px solid var(--accent);
            border-radius: 999px;
            padding: 0.6rem 1.4rem;
            font-weight: 600;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease;
            box-shadow: 0 10px 24px rgba(74, 144, 226, 0.25);
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            background: #5a9be8;
        }}

        .stButton > button:focus {{
            outline: 3px solid rgba(74, 144, 226, 0.35);
            outline-offset: 2px;
        }}

        div[data-baseweb="input"] > div {{
            background: var(--input-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
        }}

        div[data-testid="stFileUploaderDropzone"] {{
            background: var(--input-bg);
            border-radius: 16px;
            border: 1px dashed var(--card-border);
        }}

        .stCheckbox > label {{
            font-weight: 500;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--card-border);
            border-radius: 18px;
            overflow: hidden;
        }}

        .section-spacer {{
            height: 1.5rem;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_config_from_ui() -> Path:
    st.markdown("### Configuration")
    st.caption("Point to the YAML rules that define your automation logic.")

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
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    if "theme_toggle" not in st.session_state:
        st.session_state["theme_toggle"] = st.session_state["theme"] == "dark"

    with st.sidebar:
        st.markdown("## Control Center")
        st.caption("Tune automation settings, safety checks, and visual style.")
        st.toggle("Dark mode", key="theme_toggle")

    st.session_state["theme"] = "dark" if st.session_state["theme_toggle"] else "light"
    _apply_theme(st.session_state["theme"])

    with st.sidebar:
        st.divider()
        cfg_path = _load_config_from_ui()
        st.divider()
        st.subheader("Run options")
        dry_run = st.checkbox("Dry run", value=True)
        delete_empty = st.checkbox("Delete empty directories after moves", value=False)
        ledger_file = Path(st.text_input("Ledger file", value="logs/move_ledger.jsonl"))
        st.caption("Executed runs are logged for fast undo support.")

    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">Automation Studio</div>
            <div class="hero-title">Personal Automation Tool</div>
            <div class="hero-subtitle">
                Plan, preview, and execute file moves with confidence. Use the control center to
                adjust your run options and keep every action reversible.
            </div>
            <div class="hero-pills">
                <span class="pill">Human-in-the-loop</span>
                <span class="pill">Ledger-backed undo</span>
                <span class="pill">Config-driven rules</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    actions = st.session_state.get("_actions")
    cfg = st.session_state.get("_cfg")
    planned_count = len(actions) if actions else 0

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Planned Actions", planned_count)
    metric_b.metric("Dry Run", "Enabled" if dry_run else "Disabled")
    metric_c.metric("Delete Empty Dirs", "Enabled" if delete_empty else "Disabled")

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    st.subheader("Action center")
    st.caption("Preview your automation plan or roll back the last execution.")
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

        st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

        st.subheader("Execution")
        st.caption("Confirm the move list before executing. Dry runs skip file operations.")
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
    else:
        st.info("Plan a run to preview actions before executing moves.")


if __name__ == "__main__":
    main()
