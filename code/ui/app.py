from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import streamlit as st

EXAMPLES = (
    "What is the expense ratio of HDFC Large Cap?",
    "What is the lock-in period for HDFC ELSS?",
    "What is the minimum SIP for HDFC Small Cap?",
)

WELCOME = (
    "Ask factual questions about selected HDFC mutual funds. Every answer is "
    "grounded in the official fund information and includes a source."
)
DISCLAIMER = "Not investment advice"
_COVERED_FUNDS = (
    "HDFC Large Cap",
    "HDFC Flexi Cap",
    "HDFC ELSS Tax Saver",
    "HDFC Small Cap",
    "HDFC Balanced Advantage",
)

from code.ui import components as ui

st.set_page_config(
    page_title="Groww Mutual Fund FAQ Bot",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

ui.render_styles()
ui.render_header()
ui.render_hero()
ui.render_fund_chips(_COVERED_FUNDS)

if "messages" not in st.session_state:
    st.session_state.messages = []


def _ask(question: str) -> dict:
    from code.retrieval.retriever import answer_question

    return answer_question(question)


def _run_question(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    stage = st.empty()
    with stage.container():
        with st.chat_message("assistant"):
            st.html(ui.typing_indicator())
    result = _ask(question)
    stage.empty()
    st.session_state.messages.append({"role": "assistant", "result": result})


def render_answer(result: dict) -> None:
    if result.get("warning"):
        st.html(ui.warning_chip(result["warning"]))

    if not result.get("generation_error"):
        st.markdown(ui.emphasize_numbers(result["answer"]), unsafe_allow_html=True)
    else:
        st.info(
            "Answer generation is off — set MISTRAL_API_KEY in `.env` to enable "
            "Mistral. Retrieval still ran (results below)."
        )

    sources_html = ui.sources(result)
    if sources_html:
        st.html(sources_html)
    if result.get("last_updated"):
        st.html(ui.updated_note(result["last_updated"]))

    if result.get("retrieved"):
        with st.expander("Retrieved chunks (debug)"):
            for row in result["retrieved"]:
                st.markdown(
                    f"- **{row['score']}** — {row['fund_name']} · "
                    f"[{row['source_url']}]({row['source_url']})"
                )


def render_message(message: dict) -> None:
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            render_answer(message["result"])


for message in st.session_state.messages:
    render_message(message)

if st.session_state.messages:
    chosen = ui.render_chat_prompts(EXAMPLES)
else:
    ui.render_empty_state()
    chosen = ui.render_suggestion_cards(EXAMPLES)

if chosen:
    _run_question(chosen)
    render_message(st.session_state.messages[-2])
    render_message(st.session_state.messages[-1])

ui.input_helper(DISCLAIMER)

prompt = st.chat_input("Ask anything about these mutual funds…")
if prompt:
    _run_question(prompt)
    render_message(st.session_state.messages[-2])
    render_message(st.session_state.messages[-1])

ui.render_footer()