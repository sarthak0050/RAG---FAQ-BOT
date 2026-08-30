# PRD: Groww HDFC Funds FAQ Chatbot (RAG Prototype)

**Product:** Facts-only FAQ assistant for five HDFC Direct Growth funds on Groww  
**Type:** Working prototype / hobby RAG test  
**Owner:** PM (this doc)  
**Status:** Draft v1.0  
**Source of truth for corpus:** [problem_statement.txt](./problem_statement.txt)

---

## 1. Problem

Investors looking at Groww fund pages need fast, factual answers (expense ratio, SIP minimum, exit load, lock-in, riskometer, statements). Today they must scan long pages. There is no in-product FAQ bot scoped to **only** those pages, and any assistant must **not** give advice or invent numbers.

This prototype tests whether a small RAG pipeline can answer **only** from five public Groww URLs, with citations, refusals, and a tiny Streamlit UI.

---

## 2. Goals

| Goal | Success look |
|------|----------------|
| Answer factual questions from the 5-page corpus | Grounded answers with one citation URL |
| Stay facts-only | Advice / buy-sell / “what should I do” → polite refusal + educational link |
| Prove a simple RAG loop | Ingest → chunk → embed → Chroma → retrieve → Mistral → UI |
| Stay compliant for a demo | No PII, no unofficial blogs, no computed/compared returns |

**Non-goals:** production scale, auth, personalization, multi-AMC, live NAV trading, comparing funds, generating performance tables.

---

## 3. Users & job-to-be-done

- **Primary:** Curious investor on Groww, browsing HDFC funds.  
  **JTBD:** “Tell me the documented fact (expense ratio / SIP / lock-in / …) without advice.”
- **Secondary:** Builder testing RAG quality (retrieval, refusals, citations).

---

## 4. In scope

### 4.1 Corpus (exclusive)

**Website:** https://groww.in/  
**AMC:** HDFC only  
**Pages (and only these — nothing else):**

| Theme | Fund | URL |
|--------|------|-----|
| Large-cap | HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi-cap | HDFC Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Fund Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small-cap | HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Hybrid | HDFC Balanced Advantage Fund Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

Public page content only. No app backend screenshots. No third-party blogs.

### 4.2 Question types (answer)

Examples: expense ratio, ELSS lock-in, minimum SIP, exit load, riskometer / benchmark, how to download capital-gains statement (if present on those pages).

### 4.3 RAG stack (fixed)

| Stage | Choice |
|--------|--------|
| Ingestion | Fetch the 5 URLs; treat as documents |
| Chunking | Split page text into retrieval chunks (size/overlap TBD in implementation; keep chunks source-URL tagged) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face) |
| Vector store | ChromaDB |
| Retrieval | Embed question → nearest chunks from store |
| LLM | Mistral (API key) |
| UI | Streamlit; Groww-inspired colors |

---

## 5. Out of scope

- Any URL or document beyond the five links  
- Investment advice, portfolio construction, buy/sell/hold  
- Computing or comparing returns (if asked: point to official factsheet / page, do not calculate)  
- Storing or asking for PAN, Aadhaar, account numbers, OTPs, emails, phones  
- Auth, session history persistence, multi-user accounts  
- Fine-tuning, paid embedding APIs, extra vector DBs

---

## 6. Functional requirements

### FR-1 Ingest & index

- Fetch and parse the five Groww pages.  
- Chunk text; store embeddings in Chroma with metadata: `source_url`, fund name, chunk id.  
- Re-ingest is a batch/offline step for the prototype (no requirement for live crawl on every query).

### FR-2 Ask & retrieve

- User submits a question in the Streamlit UI.  
- Embed the question with the same MiniLM model.  
- Retrieve top-k chunks (k small, e.g. 3–5).  
- If retrieval is weak / off-corpus, refuse or say the fact is not in the five pages.

### FR-3 Answer generation

- Prompt Mistral with: retrieved chunks, hard rules (facts-only, ≤3 sentences, one citation, no PII, no advice, no return math).  
- Every answer includes **one clear citation link** (the Groww URL that backs the claim).  
- Every answer includes **“Last updated from sources: &lt;date&gt;”** (ingest/index date is acceptable for the prototype).  
- Answers **≤ 3 sentences** (citation + last-updated line may sit outside the three sentences).

### FR-4 Refusals

| User intent | Behavior |
|-------------|----------|
| Buy/sell/hold, “best fund”, allocation, “should I…” | Polite facts-only refusal + one relevant **educational** link (prefer Groww help/learn if used; do not invent blogs). Do not retrieve-as-advice. |
| Returns / CAGR / “which performed better” | Do not compute or compare. Direct to official factsheet or the fund page. |
| PII in the prompt | Do not store. Warn user not to share PII; answer without using those identifiers. |
| Unrelated / outside 5 pages | Say we only cover these five HDFC Direct Growth pages on Groww. |

### FR-5 UI (tiny)

- Welcome line.  
- **Three example questions** (click-to-fill or click-to-ask). Suggested:  
  1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?  
  2. What is the lock-in for HDFC ELSS Tax Saver?  
  3. What is the minimum SIP for HDFC Small Cap Fund Direct Growth?  
- Persistent note: **“Facts-only. No investment advice.”**  
- Chat input + answer with citation + last-updated.  
- Visual: Groww-like palette (dark green / Groww site colors).

### FR-6 Edge-case testing (must ship with prototype)

Documented test set covering at least:

- In-corpus fact (each fund: one question).  
- Cross-fund mix-up (“expense ratio of ELSS” vs large-cap).  
- Advice / should I buy.  
- Returns comparison.  
- PII in message.  
- Empty / gibberish query.  
- Question about a fund not in the five.  
- Capital-gains statement (answer only if in corpus; else “not on these pages”).  
- Flexi-cap via legacy slug (`hdfc-equity-fund-direct-growth`) still retrieves Flexi Cap content.

---

## 7. Non-functional requirements

- **Latency:** Prototype-quality; first answer within ~10–20s is acceptable.  
- **Privacy:** No PII persistence; no logging of identifiers.  
- **Transparency:** Citation + last-updated on every answer.  
- **Grounding:** LLM must not use knowledge outside retrieved chunks for numeric/policy facts.  
- **Secrets:** Mistral API key via env, not committed.

---

## 8. UX copy (minimum)

- **Welcome (example):** “Ask factual questions about five HDFC Direct Growth funds listed on Groww. I cite the page I used.”  
- **Disclaimer (always visible):** “Facts-only. No investment advice.”  
- **Refusal (example):** “I can’t advise on buying or selling. I only share facts from the listed Groww fund pages. Here’s an educational link: …”

---

## 9. Metrics (prototype)

| Metric | Target |
|--------|--------|
| Citation present | 100% of answers (including refusals that still show a relevant link) |
| Advice questions | 100% refused; no recommendation language |
| ≤3 sentence body | 100% of factual answers |
| Retrieval on gold FAQ set | Majority of FR-6 in-corpus questions answer correctly vs page text |
| Out-of-corpus | No fabricated fund facts |

No production SLAs.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Groww pages are JS-heavy / hard to scrape | Use a fetch method that gets readable text; fail ingest loudly if a URL is empty |
| Page layout changes | Re-run ingest; keep “last updated” honest |
| LLM hallucinates numbers | Prompt: use chunks only; if missing, say so |
| MiniLM + small corpus misses a fact | Tune chunk size / k; keep questions aligned to page headings |
| User treats bot as advisor | Disclaimer + refusal copy always on |

---

## 11. Delivery slice

**MVP (this prototype):** ingest 5 URLs → Chroma + MiniLM → Mistral answers in Streamlit with citations, last-updated, refusals, 3 example questions, edge-case test notes/script.

**Explicitly later:** more funds, live re-crawl, eval dashboard, production hosting.

---

## 12. Open decisions (implementation, not product)

- Exact chunk size / overlap and `k`.  
- Exact Groww hex colors from the live site.  
- Educational URL used on advice refusal (must stay public Groww, not a blog).  
- Factsheet handling: if the five pages link to a factsheet, **link only**; do not ingest extra URLs.
