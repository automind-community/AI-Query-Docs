"""Streamlit workspace entrypoint for AI QueryDocs."""

from __future__ import annotations

from pathlib import Path
import sys

_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st

from ui import api_client, components, styles


def init_session_state() -> None:
    """Initialize required session state keys cleanly."""
    state = st.session_state
    state.setdefault("messages", [])
    state.setdefault("documents", [])
    state.setdefault("notice", None)
    if "health" not in state:
        state.health = api_client.check_health()


def main() -> None:
    """Configure page chrome, apply styles, and render the reading workspace."""
    st.set_page_config(
        page_title=api_client.get_app_name(),
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    styles.apply()
    init_session_state()

    components.header()
    if st.session_state.messages:
        with st.container(key="transcript", height=480, border=False, autoscroll=True):
            components.thread(st.session_state.messages)
            components.render_notice()
        # A main-level chat_input goes into Streamlit's native bottom dock.
        submission = components.composer()
    else:
        with st.container(key="canvas"):
            submission = components.empty_workspace()
    components.submit(submission)


if __name__ == "__main__":
    main()
