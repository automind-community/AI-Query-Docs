"""Timeless neutral-charcoal presentation rules for the AI QueryDocs workspace."""

from __future__ import annotations

import streamlit as st

_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700&display=swap');

:root {
    --aqd-bg: #171717;
    --aqd-surface: #212121;
    --aqd-hover: #2A2A2A;
    --aqd-user-pill: #2B2B2B;
    --aqd-border: rgba(255, 255, 255, 0.10);
    --aqd-border-strong: rgba(255, 255, 255, 0.18);
    --aqd-text: #ECECEC;
    --aqd-heading: #F5F5F5;
    --aqd-muted: #9B9B9B;
    --aqd-online: #10B981;
    --aqd-offline: #E07A5F;
    --aqd-pdf-fg: #E07A5F;
    --aqd-pdf-bg: rgba(224, 122, 95, 0.14);
    --aqd-txt-fg: #A1A1AA;
    --aqd-txt-bg: rgba(161, 161, 170, 0.14);
    --aqd-cite-fg: #EED49F;
    --aqd-cite-bg: rgba(238, 212, 159, 0.13);
    --aqd-cite-border: rgba(238, 212, 159, 0.24);
}

/* Hide default Streamlit chrome while keeping layout clean */
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stDecoration"],
.stDeployButton,
footer {
    display: none !important;
}

.stApp {
    background: var(--aqd-bg);
    color: var(--aqd-text);
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp p,
.stApp textarea,
.stApp input {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stMainBlockContainer {
    max-width: none;
    padding: 0 0 1.5rem;
}

/* Sticky top navigation bar */
[data-testid="stLayoutWrapper"]:has(> .st-key-mast),
.st-key-mast {
    position: sticky;
    top: 0;
    z-index: 90;
    background: rgba(23, 23, 23, 0.88);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.st-key-mast {
    min-height: 56px;
    padding: 8px clamp(12px, 3vw, 40px);
    border-bottom: 1px solid var(--aqd-border);
    flex-wrap: nowrap !important;
}

.brand,
.byline,
.doc {
    display: flex;
    align-items: center;
    gap: 0.55rem;
}

.brand,
.hero h1,
.byline {
    font-family: "Plus Jakarta Sans", Inter, -apple-system, BlinkMacSystemFont, sans-serif;
}

.brand {
    font-weight: 600;
    font-size: 0.96rem;
    letter-spacing: -0.02em;
    color: var(--aqd-heading);
    white-space: nowrap;
}

.brand-mark {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    flex: none;
    display: block;
}

/* Top bar & pill buttons */
.st-key-mast button,
.st-key-attachments button,
.st-key-starters button {
    min-height: 32px;
    border: 1px solid var(--aqd-border);
    border-radius: 999px;
    background: var(--aqd-surface);
    color: var(--aqd-text);
    padding: 0.28rem 0.8rem;
    transition: background-color 0.15s ease, border-color 0.15s ease;
}

.st-key-mast button:hover,
.st-key-attachments button:hover,
.st-key-starters button:hover {
    background: var(--aqd-hover);
    border-color: var(--aqd-border-strong);
}

.st-key-mast button p,
.st-key-attachments button p,
.st-key-starters button p {
    font-size: 0.81rem;
    line-height: 1.25;
}

.st-key-new_chat_btn button {
    background: transparent;
    border-color: transparent;
    color: var(--aqd-muted);
}

.st-key-new_chat_btn button:hover {
    background: var(--aqd-hover);
    border-color: var(--aqd-border);
    color: var(--aqd-text);
}

.st-key-online button::before,
.st-key-offline button::before {
    content: "";
    display: inline-block;
    width: 7px;
    height: 7px;
    margin-right: 0.42rem;
    border-radius: 50%;
    flex: none;
}

.st-key-online button::before {
    background: var(--aqd-online);
}

.st-key-offline button::before {
    background: var(--aqd-offline);
}

/* Popover surfaces */
[data-testid="stPopoverBody"] {
    background: var(--aqd-surface) !important;
    border: 1px solid var(--aqd-border) !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45) !important;
}

[data-testid="stPopoverBody"] [data-testid="stHorizontalBlock"]:has(.doc):hover {
    background: var(--aqd-hover);
    border-radius: 8px;
}

/* Centered reading canvas */
.st-key-canvas {
    max-width: min(800px, calc(100% - 32px));
    margin: 1.25rem auto 0;
    gap: 0.85rem;
}

/* The transcript scrolls independently between the navigation and native dock. */
.st-key-transcript {
    min-height: 0;
    padding: 0 max(16px, calc((100% - 800px) / 2)) 24px;
    scrollbar-gutter: stable both-edges;
}
[data-testid="stBottom"] {background: var(--aqd-bg)}
[data-testid="stBottomBlockContainer"] {
    max-width: min(800px, calc(100% - 32px));
    margin: 0 auto;
    padding: 10px 0 max(14px, env(safe-area-inset-bottom));
    background: var(--aqd-bg);
}
.stMainBlockContainer:has(.st-key-transcript) {
    flex: 1 1 0;
    min-height: 0;
    padding-bottom: 0;
}
/* Streamlit inserts a flexible spacer before stBottom. Give that space to the thread. */
.stMainBlockContainer:has(.st-key-transcript) ~ :empty {flex: none}
.stMainBlockContainer:has(.st-key-transcript) > [data-testid="stVerticalBlock"] {height: 100%}
[data-testid="stLayoutWrapper"]:has(> .st-key-transcript) {
    flex: 1 1 0;
    min-height: 0;
}
[data-testid="stBottom"]:has(.st-key-composer) {flex-shrink: 0}
.quiet-notice {overflow-wrap:anywhere}
/* Empty-state hero */
.hero {
    text-align: center;
    margin: clamp(2.5rem, 12vh, 5.75rem) auto 1.15rem;
}

.hero h1 {
    margin: 0;
    font-size: clamp(1.85rem, 3.8vw, 2.65rem);
    font-weight: 600;
    line-height: 1.16;
    letter-spacing: -0.035em;
    color: var(--aqd-heading);
}

.hero p {
    color: var(--aqd-muted);
    font-size: 0.94rem;
    line-height: 1.5;
    max-width: 34rem;
    margin: 0.55rem auto 0;
}

/* Attached file chips above composer */
.st-key-attachments {
    flex-wrap: wrap !important;
    gap: 0.45rem !important;
}

.st-key-attachments button {
    background: var(--aqd-surface);
    color: var(--aqd-text);
    padding: 0.26rem 0.7rem;
}

.format,
.st-key-attachments strong {
    font: 600 0.66rem/1 Inter, sans-serif;
    letter-spacing: 0.03em;
    padding: 0.16rem 0.4rem;
    border-radius: 5px;
    text-transform: uppercase;
}

.pdf,
[class*="st-key-pill_PDF"] strong {
    color: var(--aqd-pdf-fg);
    background: var(--aqd-pdf-bg);
}

.txt,
[class*="st-key-pill_TXT"] strong {
    color: var(--aqd-txt-fg);
    background: var(--aqd-txt-bg);
}

/* ChatGPT / Claude-inspired composer */
:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInput"] {
    border: 1px solid var(--aqd-border);
    border-radius: 22px;
    background: var(--aqd-surface);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.28);
    padding: 6px 8px;
    transition: border-color 0.16s ease, box-shadow 0.16s ease;
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInput"]:focus-within {
    border-color: var(--aqd-border-strong);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.36);
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInput"] :is(div, textarea) {
    border: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
    color: var(--aqd-text);
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInput"] textarea::placeholder {
    color: var(--aqd-muted);
}

/* Native attach icon inside composer */
:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputFileUploadButton"] button {
    background: transparent !important;
    color: var(--aqd-muted) !important;
    border-radius: 999px !important;
    transition: background-color 0.15s ease, color 0.15s ease;
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputFileUploadButton"] button:hover {
    background: var(--aqd-hover) !important;
    color: var(--aqd-text) !important;
}

/* White circular send button inside composer */
:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputSubmitButton"] {
    background: #FFFFFF !important;
    color: #171717 !important;
    border-radius: 999px !important;
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    padding: 0 !important;
    transition: opacity 0.15s ease, transform 0.12s ease;
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputSubmitButton"]:hover:not(:disabled) {
    opacity: 0.9;
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputSubmitButton"]:disabled {
    background: rgba(255, 255, 255, 0.18) !important;
    color: #171717 !important;
    opacity: 0.55;
}

:is(.st-key-canvas, [data-testid="stBottom"]) [data-testid="stChatInputSubmitButton"] svg {
    fill: #171717 !important;
    color: #171717 !important;
}

/* Compact horizontal starter suggestion pills */
.st-key-starters {
    flex-wrap: wrap !important;
    justify-content: center !important;
    gap: 0.5rem !important;
    margin-top: 0.25rem;
}

.st-key-starters button {
    height: auto !important;
    min-height: 34px;
    padding: 0.38rem 0.9rem !important;
    background: var(--aqd-surface);
    border: 1px solid var(--aqd-border);
    border-radius: 999px;
}

.st-key-starters button:hover {
    background: var(--aqd-hover);
    border-color: var(--aqd-border-strong);
}

.st-key-starters button span[data-testid="stIconMaterial"] {
    color: var(--aqd-muted);
    font-size: 1rem;
}

/* Conversation thread */
.question,
.answer {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.question {
    margin: 1rem 0 0.25rem auto;
    width: fit-content;
    max-width: 82%;
    padding: 0.7rem 1.05rem;
    background: var(--aqd-user-pill);
    color: var(--aqd-text);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.55;
}

.byline {
    font-weight: 600;
    font-size: 0.87rem;
    color: var(--aqd-heading);
    margin: 0.85rem 0 0.45rem;
}

.byline .brand-mark {
    width: 22px;
    height: 22px;
    border-radius: 6px;
}

.byline small {
    color: var(--aqd-muted);
    font-size: 0.72rem;
    font-weight: 500;
}

.answer {
    color: var(--aqd-text);
    font-size: 0.96rem;
    line-height: 1.7;
}

.answer-error {
    color: #F3B3A1;
    background: rgba(224, 122, 95, 0.10);
    border: 1px solid rgba(224, 122, 95, 0.26);
    border-radius: 12px;
    padding: 0.75rem 0.95rem;
}

/* Warm ivory/amber inline citation chips */
.ref,
.doc b {
    color: var(--aqd-cite-fg);
    background: var(--aqd-cite-bg);
    border: 1px solid var(--aqd-cite-border);
    border-radius: 5px;
    padding: 0.08rem 0.36rem;
    font: 600 0.75rem Inter, sans-serif;
}

.sources-label {
    font: 600 0.7rem Inter, sans-serif;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--aqd-muted);
    margin: 0.75rem 0 0.45rem;
}

.citations {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
    gap: 0.6rem;
}

.citations article {
    background: var(--aqd-surface);
    border: 1px solid var(--aqd-border);
    border-radius: 12px;
    padding: 0.78rem 0.88rem;
    transition: background-color 0.15s ease, border-color 0.15s ease;
}

.citations article:hover {
    background: var(--aqd-hover);
    border-color: var(--aqd-border-strong);
}

.doc {
    min-width: 0;
}

.doc strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.84rem;
    font-weight: 600;
    color: var(--aqd-heading);
}

.doc small {
    white-space: nowrap;
    color: var(--aqd-muted);
    margin-left: auto;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--aqd-border);
    border-radius: 999px;
    padding: 0.12rem 0.48rem;
    font-size: 0.72rem;
}

.citations p {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    overflow-wrap: anywhere;
    color: var(--aqd-muted);
    font-size: 0.82rem;
    line-height: 1.48;
    margin: 0.48rem 0 0;
}

.quiet-notice {
    color: var(--aqd-muted);
    font-size: 0.82rem;
    padding: 0.15rem 0.25rem;
}

.quiet-notice.warn {
    color: #F3B3A1;
}

@media (max-width: 640px) {
    .st-key-mast {
        gap: 6px;
        padding: 8px 12px;
    }

    .st-key-mast button {
        padding: 0.22rem 0.56rem;
    }

    .brand {
        font-size: 0.88rem;
        gap: 0.42rem;
    }

    .brand .brand-mark {
        width: 24px;
        height: 24px;
    }

    .st-key-canvas {
        max-width: calc(100% - 24px);
        margin-top: 0.75rem;
    }

    .hero {
        margin: 2.25rem auto 1rem;
    }

    .hero h1 {
        font-size: 1.75rem;
    }

    .question {
        max-width: 92%;
    }
}

@media (prefers-reduced-motion: reduce) {
    .st-key-mast button,
    .st-key-attachments button,
    .st-key-starters button,
    .citations article {
        transition: none;
    }
}
</style>
"""


def apply() -> None:
    """Inject global neutral-charcoal styles for the Streamlit workspace."""
    st.html(_THEME_CSS)
