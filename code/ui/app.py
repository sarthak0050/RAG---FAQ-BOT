from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import streamlit as st

from code.retrieval.retriever import answer_question

GROWW_GREEN = "#00D09C"
GROWW_GREEN_DEEP = "#00A67B"
GROWW_DARK = "#10161A"
GROWW_DARKER = "#0B0F12"
GROWW_TEXT = "#EDF2EF"
GROWW_MUTED = "#8FA39A"

EXAMPLES = (
    "What is the expense ratio of HDFC Large Cap Fund Direct Growth?",
    "What is the lock-in for HDFC ELSS Tax Saver?",
    "What is the minimum SIP for HDFC Small Cap Fund Direct Growth?",
)

WELCOME = (
    "Factual answers about HDFC Direct Growth funds, drawn directly from "
    "each fund's official page. Every answer cites its source."
)
DISCLAIMER = "Facts-only · Not investment advice"
_COVERED_FUNDS = (
    "HDFC Large Cap · HDFC Flexi Cap · HDFC ELSS Tax Saver · "
    "HDFC Small Cap · HDFC Balanced Advantage"
)

st.set_page_config(
    page_title="Groww Mutual Fund FAQ Bot",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.html(
    f"""
    <style>
      .brand-row {{ display: flex; align-items: center; gap: 14px; margin-bottom: 6px; }}
      .brand-mark {{ flex: 0 0 auto; width: 46px; height: 46px; border-radius: 14px;
        background: linear-gradient(135deg, {GROWW_GREEN}, {GROWW_GREEN_DEEP});
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 6px 20px rgba(0, 208, 156, 0.25); }}
      .brand-title {{ font-size: 26px; font-weight: 800; letter-spacing: 0.6px;
        color: {GROWW_GREEN}; line-height: 1.15; margin: 0; }}
      .brand-sub {{ margin-top: 4px; color: {GROWW_MUTED}; font-size: 13px;
        font-weight: 500; letter-spacing: 0.3px; }}
    </style>
    <div class="brand-row">
      <div class="brand-mark">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
          <path d="M4 20V4" stroke="#0B0F12" stroke-width="2.4" stroke-linecap="round"/>
          <path d="M4 16l6-4 4 2 6-7" stroke="#0B0F12" stroke-width="2.4"
                stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="17" cy="9" r="2.2" fill="#0B0F12"/>
        </svg>
      </div>
      <div>
        <div class="brand-title">GROWW <span style="color:{GROWW_MUTED};">MUTUAL FUND FAQ BOT</span></div>
        <div class="brand-sub">HDFC Direct Growth &mdash; facts, with sources</div>
      </div>
    </div>
    """
)

st.markdown(WELCOME)
st.markdown(f"*{DISCLAIMER}* · **Covers:** {_COVERED_FUNDS}")

if "messages" not in st.session_state:
    st.session_state.messages = []


def _ask(question: str) -> dict:
    with st.spinner("Searching the fund documents…"):
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
        st.chat_message("user", avatar="🙂").markdown(message["content"])
    else:
        with st.chat_message("assistant", avatar="📈"):
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

st.markdown(
    f"Powered by Groww, embeddings & Mistral · Facts-only, sourced from fund pages · {DISCLAIMER}"
)