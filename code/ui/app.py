from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import streamlit as st

from code.retrieval.retriever import answer_question

GROWW_GREEN = "#00D09C"
GROWW_DARK = "#10161A"
GROWW_DARKER = "#0B0F12"

EXAMPLES = (
    "What is the expense ratio of HDFC Large Cap Fund Direct Growth?",
    "What is the lock-in for HDFC ELSS Tax Saver?",
    "What is the minimum SIP for HDFC Small Cap Fund Direct Growth?",
)

WELCOME = (
    "Ask factual questions about five HDFC Direct Growth funds listed on Groww. "
    "I cite the page I used."
)
DISCLAIMER = "Facts-only. No investment advice."

_COVERED_FUNDS = (
    "HDFC Large Cap, HDFC Flexi Cap, HDFC ELSS Tax Saver, "
    "HDFC Small Cap, HDFC Balanced Advantage"
)

st.set_page_config(
    page_title="Groww Mutual Fund FAQ Bot",
    page_icon=":chart_with_upwards_trend:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background: {GROWW_DARK}; }}
      [data-testid="stHeader"] {{ background: {GROWW_DARK}; }}
      .block-container {{
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 860px;
      }}
      .groww-title {{
        color: {GROWW_GREEN};
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.4px;
        line-height: 1.4;
        margin: 0 0 8px 0;
        overflow: visible;
      }}
      .groww-welcome {{ color: #E3E6E4; font-size: 16px; line-height: 1.5; margin: 0; }}
      .groww-note {{
        background: {GROWW_DARKER};
        border-left: 4px solid {GROWW_GREEN};
        color: #B9C2BC;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        line-height: 1.5;
        margin: 12px 0 20px 0;
      }}
      .stButton > button {{
        width: 100%;
        min-height: 76px;
        background: {GROWW_DARKER};
        border: 1px solid #2A3530;
        border-radius: 12px;
        color: {GROWW_GREEN};
        font-size: 13px;
        font-weight: 600;
        line-height: 1.45;
        text-align: left;
        padding: 12px 14px;
        white-space: normal;
        box-shadow: none;
        transition: border-color 0.15s ease, transform 0.1s ease;
      }}
      .stButton > button:hover {{
        border-color: {GROWW_GREEN};
        transform: translateY(-1px);
      }}
      [data-testid="stHorizontalBlock"] {{ gap: 1rem; }}
      .stButton {{ margin-bottom: 8px; }}
      .chat-held {{ color: #F0F3F1; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="groww-title">GROWW MUTUAL FUND FAQ BOT</div>', unsafe_allow_html=True)
st.markdown(f'<div class="groww-welcome">{WELCOME}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="groww-note">{DISCLAIMER} · Covers only: {_COVERED_FUNDS}</div>',
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def _ask(question: str) -> dict:
    with st.spinner("Retrieving from the five Groww pages…"):
        return answer_question(question)


def render_answer(result: dict) -> None:
    if result.get("warning"):
        st.warning(result["warning"])

    if not result.get("generation_error"):
        st.markdown(result["answer"])
    else:
        st.info(
            "Answer generation is off — set MISTRAL_API_KEY in `.env` to enable "
            "Mistral. Retrieval still ran (results below)."
        )

    if result.get("source_url"):
        st.markdown(f"**Source:** [{result['source_url']}]({result['source_url']})")
    if result.get("last_updated"):
        st.markdown(f"*Last updated from sources: {result['last_updated']}*")

    if result.get("retrieved"):
        with st.expander("Retrieved chunks (debug)"):
            for row in result["retrieved"]:
                st.markdown(
                    f"- **{row['score']}** — {row['fund_name']} · "
                    f"[{row['source_url']}]({row['source_url']})"
                )


def render_message(message: dict) -> None:
    if message["role"] == "user":
        st.chat_message("user").markdown(
            f'<span class="chat-held">{message["content"]}</span>',
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant"):
            render_answer(message["result"])


def handle(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    result = _ask(question)
    st.session_state.messages.append({"role": "assistant", "result": result})
    render_message(st.session_state.messages[-2])
    render_message(st.session_state.messages[-1])


for message in st.session_state.messages:
    render_message(message)

cols = st.columns(len(EXAMPLES))
for col, example in zip(cols, EXAMPLES):
    if col.button(example, use_container_width=True):
        handle(example)

prompt = st.chat_input("Ask a factual question about an HDFC fund…")
if prompt:
    handle(prompt)