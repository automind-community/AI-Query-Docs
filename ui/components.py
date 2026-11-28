"""Navigation, popover source manager, native composer, and reading canvas."""

from __future__ import annotations

from base64 import b64encode
from html import escape
import re
from typing import Any, Sequence

import streamlit as st

from ui import api_client as api

# Monochrome minimal document SVG on a #262626 rounded tile with crisp border.
MARK = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" '
    'viewBox="0 0 32 32" aria-hidden="true">'
    '<rect x="0.75" y="0.75" width="30.5" height="30.5" rx="8.5" '
    'fill="#262626" stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>'
    '<g fill="none" stroke="#ECECEC" stroke-width="1.65" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M11 8.5h6.5L22 13v10.5H11z"/>'
    '<path d="M17.5 8.5V13H22"/>'
    '<path d="M13.8 16.8h5.4M13.8 19.8h3.6" stroke="#A1A1AA"/>'
    "</g></svg>"
)

# Streamlit sanitizes inline SVG tags; an SVG data URI keeps the vector mark intact.
MARK_URL = "data:image/svg+xml;base64," + b64encode(MARK.encode()).decode()

PROMPTS: tuple[tuple[str, str], ...] = (
    ("Summarize key points", "notes"),
    ("Extract requirements", "checklist"),
    ("Find dates & deadlines", "event"),
)


def brand_row(*, compact: bool = False, cited: bool = False) -> None:
    """Render the monochrome AI QueryDocs brand mark and title."""
    css = "byline" if compact else "brand"
    tag = "<small>Cited answer</small>" if cited else ""
    st.html(
        f'<div class="{css}">'
        f'<img class="brand-mark" src="{MARK_URL}" alt="" />'
        f"AI QueryDocs {tag}"
        "</div>"
    )


def type_badge(kind: str) -> str:
    """Return an HTML micro-badge for PDF or TXT document types."""
    normalized = kind.upper()
    if normalized not in ("PDF", "TXT"):
        return ""
    return f'<em class="format {normalized.lower()}">{normalized}</em>'


def refresh_health() -> None:
    """Refresh cached API health status in session state."""
    st.session_state.health = api.check_health()


def remove_doc(name: str) -> None:
    """Remove a session document via the api_client preview adapter."""
    state = st.session_state
    result = api.remove_document(name, state.documents)
    if result.ok and isinstance(result.data, dict):
        state.documents = list(result.data.get("documents") or [])
    state.notice = None


def clear_all_docs() -> None:
    """Clear all session-tracked documents."""
    state = st.session_state
    state.documents = []
    state.notice = None


def _render_sources_popover() -> None:
    """Render the sleek Sources (N) dropdown popover in the top navbar."""
    state = st.session_state
    docs: list[dict[str, Any]] = state.documents
    with st.popover(f"Sources ({len(docs)})", key="sources_popover"):
        st.caption("Text-based PDF & TXT up to 10 MB · No OCR · Session preview")
        if not docs:
            st.caption(
                "Attach PDF or TXT files using the paperclip inside the message bar."
            )
            return

        for idx, doc in enumerate(docs):
            name = str(doc.get("filename") or f"document-{idx}")
            file_type = str(doc.get("file_type") or "")
            size_label = str(doc.get("size_label") or "")
            with st.container(horizontal=True, vertical_alignment="center"):
                with st.container():
                    st.html(
                        f'<div class="doc">{type_badge(file_type)}'
                        f"<strong>{escape(name)}</strong>"
                        f"<small>{escape(size_label)}</small></div>"
                    )
                st.button(
                    "×",
                    key=f"pop_remove_{idx}_{name}",
                    help=f"Remove {name}",
                    type="tertiary",
                    on_click=remove_doc,
                    args=(name,),
                )

        st.button(
            "Clear all",
            key="pop_clear_all",
            type="tertiary",
            on_click=clear_all_docs,
        )


def header() -> None:
    """Render the sticky slim top navigation bar."""
    state = st.session_state
    with st.container(
        horizontal=True,
        vertical_alignment="center",
        gap="small",
        key="mast",
    ):
        with st.container():
            brand_row()
        _render_sources_popover()
        if state.messages:
            st.button(
                "New chat",
                key="new_chat_btn",
                type="tertiary",
                on_click=state.messages.clear,
            )
        status = "Online" if state.health.ok else "Offline"
        with st.popover(status, key=status.lower()):
            try:
                st.code(api.get_api_base_url() + "/health", language=None)
            except ValueError as exc:
                st.text(str(exc))
            if state.health.ok:
                st.json(state.health.data)
            else:
                st.text(state.health.error or "Unable to reach the FastAPI server.")
            st.button("Refresh", key="refresh_health_btn", on_click=refresh_health)


def attachments() -> None:
    """Render compact removable file chips above the composer when docs exist."""
    docs: list[dict[str, Any]] = st.session_state.documents
    if not docs:
        return

    with st.container(horizontal=True, key="attachments", gap="small"):
        for idx, doc in enumerate(docs):
            name = str(doc.get("filename") or f"file-{idx}")
            kind = str(doc.get("file_type") or "")
            size_label = str(doc.get("size_label") or "")
            label = name if len(name) <= 26 else name[:23] + "…"
            st.button(
                f"**{kind}** · {label} · {size_label} ×",
                key=f"pill_{kind}_{idx}",
                help=f"Remove {name}",
                on_click=remove_doc,
                args=(name,),
            )


def _format_citations(text: str, source_count: int) -> str:
    """Escape assistant text and highlight valid [N] citation markers."""
    escaped = escape(text)
    return re.sub(
        r"\[(\d{1,5})\]",
        lambda m: (
            f'<b class="ref">{m[0]}</b>'
            if 1 <= int(m[1]) <= source_count
            else m[0]
        ),
        escaped,
    )


def thread(messages: Sequence[dict[str, Any]]) -> None:
    """Render the conversation messages and citation source cards."""
    for msg in messages:
        if msg.get("role") == "user":
            st.html(f'<div class="question">{escape(str(msg.get("content") or ""))}</div>')
            continue

        sources = list(msg.get("sources") or [])
        is_error = bool(msg.get("is_error", False))
        brand_row(compact=True, cited=bool(sources) and not is_error)
        if is_error:
            st.html(
                f'<div class="answer answer-error">{escape(str(msg.get("content") or ""))}</div>'
            )
            continue

        content = _format_citations(str(msg.get("content") or ""), len(sources))
        st.html(f'<div class="answer">{content}</div>')
        if not sources:
            continue

        cards = []
        for idx, source in enumerate(sources, start=1):
            raw_page = source.get("page")
            page_html = (
                f"<small>Page {raw_page}</small>"
                if isinstance(raw_page, int) and not isinstance(raw_page, bool) and raw_page > 0
                else ""
            )
            doc_name = str(source.get("doc") or "Unknown document")
            kind = doc_name.rsplit(".", 1)[-1].upper() if "." in doc_name else ""
            snippet = str(source.get("snippet") or "").strip() or "No excerpt provided."
            cards.append(
                "<article>"
                f'<div class="doc"><b>[{idx}]</b>{type_badge(kind)}'
                f"<strong>{escape(doc_name)}</strong>{page_html}</div>"
                f"<p>{escape(snippet)}</p>"
                "</article>"
            )
        st.html(
            '<div class="sources-label">Sources</div>'
            f'<div class="citations">{"".join(cards)}</div>'
        )


def render_notice() -> None:
    """Render and consume any quiet status or validation notice from session state."""
    notice = st.session_state.pop("notice", None)
    if not isinstance(notice, dict):
        return
    if notice.get("ok"):
        st.html(f'<div class="quiet-notice">{escape(str(notice["ok"]))}</div>')
    for err in notice.get("errors") or []:
        st.html(f'<div class="quiet-notice warn">{escape(str(err))}</div>')


def _ingest_uploaded_files(files: Sequence[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate and add attached files to session state via api_client.upload_documents."""
    candidates = [
        {"name": f.name, "size_bytes": f.size}
        for f in files
        if hasattr(f, "name") and hasattr(f, "size")
    ]
    if not candidates:
        return [], []

    result = api.upload_documents(candidates, st.session_state.documents)
    data = result.data if isinstance(result.data, dict) else {}
    added = list(data.get("added") or [])
    rejected = list(data.get("rejected") or [])
    if added:
        st.session_state.documents.extend(added)
    return added, rejected


def _extract_submission(raw_submission: Any) -> tuple[str, list[Any]]:
    """Normalize either ChatInputValue or starter string into (text, files)."""
    if isinstance(raw_submission, str):
        return raw_submission, []
    text = str(getattr(raw_submission, "text", "") or "")
    files = list(getattr(raw_submission, "files", None) or [])
    return text, files


def composer():
    """The caller determines whether Streamlit mounts the inline or docked widget."""
    return st.chat_input(
        "Ask anything about your documents...",
        accept_file="multiple",
        file_type=["pdf", "txt"],
        max_upload_size=api.MAX_UPLOAD_SIZE_MB,
        key="composer",
    )


def empty_workspace():
    st.html(
        '<div class="hero"><h1>What can I help you find?</h1>'
        "<p>Explore your documents with page-level citations.</p></div>"
    )
    render_notice()
    attachments()
    submission = composer()
    with st.container(horizontal=True, horizontal_alignment="center", key="starters"):
        for label, icon in PROMPTS:
            if st.button(label, key=f"starter_{icon}", icon=f":material/{icon}:"):
                submission = label
    return submission


def submit(submission) -> None:
    if submission is None:
        return
    raw_text, attached_files = _extract_submission(submission)
    cleaned_text = raw_text.strip()

    if attached_files:
        added, rejected = _ingest_uploaded_files(attached_files)
        count = len(added)
        st.session_state.notice = {
            "ok": f"{count} source{'s' if count != 1 else ''} attached to session preview." if count else "",
            "errors": rejected,
        }
    if not cleaned_text:
        if not attached_files:
            st.session_state.notice = {"ok": "Enter a question to continue."}
        st.rerun()

    messages = st.session_state.messages
    messages.append({"role": "user", "content": cleaned_text})
    with st.spinner("Finding an answer..."):
        result = api.ask_question(cleaned_text)

    if result.ok and isinstance(result.data, dict):
        messages.append(
            {
                "role": "assistant",
                "content": str(result.data.get("answer") or ""),
                "sources": list(result.data.get("sources") or []),
                "is_error": False,
            }
        )
    else:
        messages.append(
            {
                "role": "assistant",
                "content": result.error or "Unable to reach the FastAPI server.",
                "sources": [],
                "is_error": True,
            }
        )
    st.rerun()
