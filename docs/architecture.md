# Architecture: Groww HDFC Funds FAQ Chatbot (RAG Prototype)

**Status:** Draft v1.0  
**Scope:** [PRD](./PRD.md) only — five Groww HDFC Direct Growth URLs, facts-only FAQ, MiniLM + Chroma + Mistral + Streamlit.  
**Out of this document:** production hosting, extra funds/URLs, auth, session store, paid embeddings, additional vector DBs, live crawl per query, eval dashboards.

---

## 1. System context

Offline **index** job builds a Chroma collection from the five public pages. Online **ask** path: Streamlit → same embedding model → Chroma top-k → Mistral (grounded) → answer with one citation and last-updated date.

```
                    ┌─────────────────────────────────────┐
                    │  Corpus (exclusive, PRD §4.1)       │
                    │  5 Groww HDFC Direct Growth URLs    │
                    └─────────────────┬───────────────────┘
                                      │ fetch once (batch)
                                      ▼
┌──────────────┐  chunks   ┌─────────────┐  vectors  ┌──────────┐
│ Data loading │──────────▶│  Chunking   │──────────▶│ Embedding│
└──────────────┘           └─────────────┘  MiniLM   └────┬─────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │ Vector store│
                                                   │  ChromaDB   │
                                                   └──────┬──────┘
                                                          │ similarity
┌──────────────┐  question ┌─────────────┐  q-embed  │
│ Streamlit UI │──────────▶│  Retrieval  │───────────┘
└──────┬───────┘           └──────┬──────┘
       │                          │ top-k + metadata
       │                          ▼
       │                   ┌─────────────┐
       │                   │ Mistral API │  facts-only prompt
       │                   └──────┬──────┘
       │                          │ ≤3 sentences + 1 citation
       ◀──────────────────────────┘  + Last updated from sources
```

**Hard boundaries (PRD):** public pages only; no PII storage; no return computation; no advice; factsheet links are **not** ingested.

---

## 2. Components (PRD stack only)

| Component | Role |
|-----------|------|
| Data loader | HTTP fetch of the five URLs; extract readable text; fail if empty |
| Chunker | Split page text; tag `source_url`, fund name, chunk id |
| Embedder | `sentence-transformers/all-MiniLM-L6-v2` for documents **and** questions |
| Vector store | ChromaDB; persists indexed chunks + embeddings + metadata |
| Retriever | Embed query → top-k (3–5) nearest chunks; weak-hit → not-in-corpus |
| Generator | Mistral API (key from env); grounded on retrieved chunks |
| UI | Streamlit; Groww-like colors; welcome, 3 examples, facts-only note |
| Retrieval tests | Documented gold set from PRD FR-6; run against retriever (and refusals) |

---

## 3. Phase A — Data loading

**Purpose:** Produce five documents, nothing else.

**Inputs:** The five URLs in PRD §4.1 (Flexi-cap uses legacy slug `hdfc-equity-fund-direct-growth`).

**Process:**

1. Fetch each URL (public GET only).
2. Parse to readable text (PRD risk: JS-heavy pages — loader must still obtain text or **fail loudly**).
3. Attach document metadata: `source_url`, fund display name, theme (large-cap / flexi-cap / ELSS / small-cap / hybrid).
4. Record **ingest timestamp** → used later as `Last updated from sources: <date>`.
5. Reject empty body; do not substitute other URLs, blogs, screenshots, or factsheet files.

**Outputs:** Five `{text, source_url, fund_name, ingested_at}` documents.

**Not in this phase:** live re-fetch on every user question (PRD: batch/offline re-ingest only).

---

## 4. Phase B — Chunking

**Purpose:** Split each document so MiniLM retrieval can hit FAQ-style facts (expense ratio, SIP, exit load, lock-in, riskometer/benchmark, capital-gains statement if present).

**Inputs:** Phase A documents.

**Process:**

1. Split text into chunks (size/overlap: implementation choice; PRD leaves TBD).
2. Every chunk **must** carry: `source_url`, fund name, `chunk_id`.
3. Do not merge text across the five URLs (avoids cross-fund mix-ups at index time).

**Outputs:** List of chunks `{chunk_id, text, source_url, fund_name}`.

---

## 5. Phase C — Embedding

**Purpose:** One vector space for corpus and queries.

**Model (fixed):** Hugging Face `sentence-transformers/all-MiniLM-L6-v2`.

**Process:**

1. Embed each chunk text with MiniLM.
2. At query time, embed the user question with the **same** model (PRD FR-2).
3. No other embedding API; no fine-tuning.

**Outputs:** `embedding[]` aligned 1:1 with chunks; query embedding at ask time.

---

## 6. Phase D — Vector store

**Purpose:** Persist chunk vectors + metadata for nearest-neighbor lookup.

**Store (fixed):** ChromaDB.

**Collection contents:**

| Field | Use |
|--------|-----|
| embedding | MiniLM vector |
| document / text | chunk body for the LLM |
| `source_url` | single citation link |
| `fund_name` | grounding / debug |
| `chunk_id` | identity |
| ingest date (collection or metadata) | last-updated line |

**Process:** Upsert all chunks in one offline index run. Prototype may wipe-and-rebuild on re-ingest.

**Not in this phase:** a second database, user session tables, PII logs.

---

## 7. Phase E — Retrieval logic

**Purpose:** Map a question to the right page chunks, or declare miss; then generate per PRD FR-3/FR-4.

**Path:**

1. **UI** receives question (or one of three example questions).
2. **PII gate:** if PAN / Aadhaar / account / OTP / email / phone appear — do not store; warn; strip identifiers before embed/LLM.
3. **Intent gate (before or instead of treating retrieval as advice):**
   - Advice / should I buy-sell / best fund / allocation → refusal + one Groww educational link; **do not** use retrieved chunks as a recommendation.
   - Returns / CAGR / which performed better → do not compute; point to factsheet **link** or the fund page (do not ingest factsheet).
4. **Embed** remaining factual questions with MiniLM.
5. **Query Chroma** for top-k (k ≈ 3–5).
6. **Weak / off-corpus:** if scores are low or chunks clearly do not support the ask (including funds not in the five) → “only these five HDFC Direct Growth pages on Groww” / fact not on these pages. No fabricated numbers.
7. **Prompt Mistral** with: top-k texts, rules (facts-only, chunks only, ≤3 sentences, one citation URL from chunk metadata, no advice, no return math).
8. **Compose response:** answer body + **one** `source_url` + `Last updated from sources: <ingest date>`.

**Citation rule:** citation URL is the Groww page of the supporting chunk(s); if multiple funds appear in top-k, prefer the fund named in the question.

---

## 8. Phase F — Retrieval testing

**Purpose:** Prove retrieval (and gates) against PRD FR-6 and prototype metrics — not a production eval platform.

**How:** A documented test set (script or checklist) that calls the **same** embed + Chroma path (and refusal gates). Compare retrieved `source_url` / fund to expected page; for generation tests, check citation present, ≤3 sentences, no advice language.

**Required cases (PRD FR-6):**

| ID | Case | Expect |
|----|------|--------|
| T1 | In-corpus fact, **each** of the five funds | Top hit(s) from that fund’s URL |
| T2 | Cross-fund mix-up (e.g. ELSS expense ratio vs large-cap) | ELSS URL, not large-cap |
| T3 | Advice / should I buy | Refusal; no recommendation; educational link |
| T4 | Returns comparison | No computed/compared returns; factsheet or page link |
| T5 | PII in message | Not stored; warning; no identifier in logs |
| T6 | Empty / gibberish | No invented fund facts |
| T7 | Fund not in the five | Out-of-corpus message |
| T8 | Capital-gains statement | Answer only if in retrieved page text; else not on these pages |
| T9 | Flexi-cap via legacy slug | Chunks from `hdfc-equity-fund-direct-growth` retrieve as Flexi Cap |

**Pass bar (PRD §9):** majority of in-corpus gold questions retrieve the correct page; out-of-corpus never fabricates; advice 100% refused; citation on answers.

Re-run after re-ingest when page layout changes.

---

## 9. Query-time vs index-time

| | Index (offline) | Ask (online) |
|--|-----------------|--------------|
| Phases | A → B → C → D | E (embed + Chroma + gates + Mistral + UI) |
| Network | Five Groww URLs | Mistral API only (pages not re-fetched) |
| Secrets | None required for public fetch | `MISTRAL_API_KEY` in env |

Latency target: first answer ~10–20s (prototype).

---

## 10. What this architecture will not add

Anything PRD §5 / §11 “later”: extra URLs, live crawl, auth, multi-user history, extra vector stores, fine-tuning, performance tables, production SLAs.
