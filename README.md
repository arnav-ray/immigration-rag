# German Immigration Law RAG

> ⚠️ **Learning project — built and documented
> in public.** This is not a finished product.
> It is an active learning exercise in AI
> engineering, documented openly so others can
> follow the same path. Expect rough edges.
> Feedback welcome.

---

An on-premise AI assistant for German immigration
law — built for privacy, built for control, and
built to explore what autonomous legal guidance
could look like at the local hardware level.

---

## The problem this solves

German immigration law is genuinely complex.
AufenthG alone runs to 650+ sections. FreizügG/EU
adds a completely separate legal regime for EU
citizens that is frequently confused with domestic
law. BeschV governs work permit approvals with
its own logic.

For individuals navigating this system, the
options are currently: pay for a lawyer
(expensive), use official government portals
(incomplete, fragmented across authorities),
or search the internet (unverified, often
outdated).

For organisations — HR departments, relocation
consultancies, law firms — processing employee
immigration queries against actual statute is
manual, slow, and creates liability when wrong.

This project demonstrates a different approach:
an AI system that reads the actual law, cites
the exact § it draws from, and runs entirely
on your own hardware.

---

## Why on-premise matters

Immigration queries contain sensitive personal
data — nationality, family status, employment
situation, residence history. Sending this to
a cloud API raises immediate questions:

- **GDPR compliance**: who processes the data,
  under which legal basis, in which jurisdiction?
- **Data sovereignty**: US cloud providers
  operate under US law regardless of where
  servers are physically located.
- **Professional liability**: legal and HR
  professionals cannot casually route client
  data through third-party AI services.
- **Cost at scale**: per-query API pricing
  becomes significant at volume.

This system runs entirely on a local GPU.
Zero data leaves the machine. No API keys
for core queries. No per-query costs. No
terms-of-service exposure.

---

## Why RAG — not just a chatbot?

A standard LLM has legal knowledge baked into
its training weights. For a legal use case, this
creates three specific failure modes:

**1. Hallucinated § numbers.**
LLMs confidently cite §§ that do not exist, or
cite the right permit name with the wrong §.
§ 19a was the Blue Card — it was replaced by
§ 18g in the 2023 Fachkräfte­einwanderungs­gesetz
reform. A model trained before 2023 cites the
wrong §. When a user relies on a cited §, a
wrong citation is worse than no answer.

**2. Stale parametric memory.**
German immigration law changes by statute. The
2023 reform restructured the entire skilled
worker chapter. An LLM trained before that reform
describes the old architecture. A RAG system
retrieves from the current statute file — rebuild
the index when the law changes.

**3. No verifiability.**
A chatbot gives an answer. A RAG system shows
the exact German text it drew from — the user
reads the § themselves and decides whether to
rely on the answer. For legal decisions,
verifiability is not optional.

**RAG solves all three:**
- Every answer is grounded in retrieved §§,
  not parametric memory — hallucination is
  structurally harder
- The index is rebuilt from the current statute
  whenever the law changes
- The source panel shows exact German § text —
  the user can verify every factual claim

---

## Why local models work for this

**Mistral NeMo 12B** (tested, functional):
- Built by Mistral AI — a French company,
  EU jurisdiction, EU data governance norms.
- 12B parameters fits in consumer GPU VRAM
  (8GB+).
- Strong multilingual capability via Tekken
  tokeniser — handles German legal text well.
- Good starting point if VRAM is limited or
  EU model provenance is a priority.

**Qwen 2.5 14B** (current default, recommended):
- Stronger reasoning at comparable hardware
  cost — better at multi-condition legal queries
  and cross-§ synthesis.
- Native tool calling support via Ollama —
  essential for future agentic layers.
- Slightly higher VRAM (~9GB) but fits on any
  modern workstation GPU.
- Better choice if reasoning quality matters
  more than model provenance.

Both run via [Ollama](https://ollama.ai) with
no configuration beyond a single pull command.
The pipeline is model-agnostic — swap the LLM
name without changing anything else.

---

## What it does today

Ask questions in English or German. The system
retrieves the relevant §§ from statute, quotes
the exact German legal text, and explains in
plain language. Every answer cites the §§ it
drew from. Users can verify the source text
directly in the interface.

**Key features (v2 system):**
- Cross-lingual retrieval — ask in English,
  retrieve from German legal text. LLM query
  expansion translates English concepts to
  German legal terms before embedding.
- § priority boost — name a § explicitly and
  it surfaces first regardless of cosine score.
- Multilingual reranking — cross-encoder scores
  query-chunk relevance in German; top 5 go
  to the LLM.
- RAG Insight panel — real-time cosine
  similarity and reranker scores for every
  retrieved chunk, with USED/NOT USED markers.
- Model selector — any Ollama model selectable
  in the sidebar without restarting.
- Compare mode — run two models side by side
  on the same retrieved chunks for benchmarking.
- Conversation memory — last 6 turns retained
  for follow-up questions.

**Independent legal evaluation results:**

| Query | Score | Notes |
|-------|-------|-------|
| Blue Card salary requirement | 8/10 | Correct §, correct mechanism |
| EU citizen rights in Germany | 7.5/10 | Three-phase structure correct |
| Non-EU spouse of EU citizen | 8/10 | Correct regime, no invented requirements |
| Non-EU spouse of German citizen | 7.5/10 | Correct §28/§31 routing |

Scores from an external qualified legal expert.
Full evaluation history — including a documented
regression from 6/10 to 3.5/10 and its root
cause — in the learning journal.

**Legal corpus:**

| Law | Applies to | Chunks |
|-----|-----------|--------|
| AufenthG | Non-EU nationals | ~270 |
| FreizügG/EU | EU citizens and family | ~23 |
| BeschV | Work permit approvals | ~48 |

---

## Technical architecture — how a query flows

### Stage 0: Document preparation (offline)

```
gesetze-im-internet.de HTML
    ↓
ingest_pdf.py (Docling)
    ↓
Structured Markdown — one file per law
    ↓
build_db.py
    ↓
  § header regex splits text at every § boundary
  → preamble + ToC blocks filtered out
  → § blocks exceeding 10,000 chars split at
    nearest blank line (heading preserved in
    sub-chunks for metadata continuity)
  → each chunk tagged: law + § number metadata
    ↓
bge-m3 embeds every chunk (1024-dim, multilingual)
    ↓
VectorStoreIndex saved to data_vector_store/
```

### Stage 1–9: Query time (per user message)

```
User query (English or German)
    ↓
[Stage 1] Broad query detection
  → taxonomy questions (e.g. "what permits exist?")
    get top_k=35; others get top_k=20

[Stage 2] LLM query expansion
  → LLM generates the German legal terms, §
    numbers, and Absatz references most relevant
    to the query's actual conditions
  → expanded terms prepended to embedding query
  → falls back to original query on error

[Stage 3] Primary vector retrieval
  → bge-m3 embeds the expanded query
  → cosine similarity against all chunks,
    top-k candidates returned

[Stage 4] Static term expansion (XL_TERMS)
  → known English→German permit name pairs
    trigger a secondary retrieval pass
  → unique additional chunks merged into
    the candidate set

[Stage 5] Taxonomy dual-query
  → for broad permit questions, a second
    German-language query anchors § 4 AufenthG
    (the formal list of residence titles)
  → prevents broad questions returning only
    one permit type

[Stage 6] § priority boost
  → if user explicitly named a § (e.g. "§ 18g"),
    all chunks from that § are sorted to position
    0 in the candidate list before reranking
  → ensures the directly-named § is always
    in the reranker's input

[Stage 7] Cosine score capture
  → all candidate similarity scores recorded
    for display in the RAG Insight panel

[Stage 8] Multilingual cross-encoder reranking
  → bge-reranker-v2-m3 scores every
    query-chunk pair (0–1 scale, multilingual)
  → top 5 by reranker score passed to LLM
  → reranker scores also displayed in
    RAG Insight panel

[Stage 9] Second retrieval pass (if needed)
  → if best reranker score < 0.1, retrieval
    reruns using only the expanded terms
    (top_k=10), merges results, re-ranks
  → prevents generating from irrelevant context
    ↓
[Stage 10] LLM generation
  → system prompt: cite §§, quote German text,
    explain in plain language, match query language
  → last 6 conversation turns injected for
    follow-up awareness
  → answer generated from top-5 reranked chunks
    ↓
Cited answer + source panel + RAG Insight panel
```

**Why each stage exists:**

| Stage | Why it matters |
|-------|---------------|
| LLM expansion | English queries don't match German legal vocabulary — cosine fails without translation |
| Static XL_TERMS | LLM expansion misses permit names if model echoes the question instead of expanding it |
| Taxonomy dual-query | Broad "what permits exist?" questions otherwise return a single permit type |
| § priority boost | Named § queries deserve exact match priority over cosine proximity |
| Cross-encoder reranking | Cosine measures embedding proximity; cross-encoder measures actual query-answer relevance |
| Second retrieval pass | Catches failure mode where initial retrieval set contains nothing relevant |

**Chunking decision — one § per chunk:**

Legal conditions are often split across multiple
Absätze within a single §. If a chunk boundary
falls mid-§, the retriever may return the second
half of a condition without the first half, and
the LLM answers from incomplete context. The §
header splitter ensures every chunk is one
complete legal section. Overflow protection
handles §§ that exceed the token limit: they
are split at the nearest blank line, with the
heading line preserved in every sub-chunk so
metadata extraction still fires correctly.

---

## How to run

**Requirements:** NVIDIA GPU 8GB+ VRAM,
[Ollama](https://ollama.ai), Python 3.11+.
Run on mains power — battery throttling causes
GPU offloading and timeout errors.

```bash
# Pull an LLM
ollama pull qwen2.5:14b

# Install dependencies
pip install -r requirements.txt

# Download AufenthG, FreizügG/EU, BeschV from
# gesetze-im-internet.de as HTML
# Convert with Docling, place .md in data_output/

# Build vector index
python build_db.py

# Run
streamlit run app.py
```

The embedding model (`BAAI/bge-m3`, ~1.2 GB)
and reranker (`BAAI/bge-reranker-v2-m3`, ~1.1 GB)
download automatically from HuggingFace on first
run. No manual setup required.

---

## Install as a Claude Skill

This project ships with a Claude Skill that
teaches Claude how to operate, troubleshoot,
and extend the system.

**Install in Claude Code:**
1. Copy the `german-immigration-rag/` folder
   to your Claude Code skills directory
   (`~/.claude/skills/` on Mac/Linux)
2. The skill loads automatically when you ask
   about installing, running, or extending
   the system

**What the skill enables:**
- Step-by-step setup and database build guide
- Model configuration and switching
- Retrieval quality troubleshooting
- Instructions for extending the corpus

---

## Known limitations

- Chunking can split very long §§ across nodes
  when a single § runs to 15,000+ characters —
  the retriever may return the second half of
  a condition without the first. Mitigation:
  overflow split preserves heading context.
- Citizenship and naturalisation require StAG —
  not in corpus. System states this explicitly
  when asked.
- Asylum law (AsylG) and social benefits (SGB)
  are out of scope.
- The system prompt in this repository is a
  functional stub. The full production prompt
  was developed through iterative legal
  evaluation and is not included here.
- Web search synthesis (optional feature) is
  stateless — conversation history is not
  passed to the web synthesis call.
- Run on mains power. Battery throttling causes
  GPU offloading and request timeout errors.

---

## How the architecture evolved

This is a learning project and the architecture
has changed substantially through iteration:

**v1 (public code baseline):**
- Single-pass retrieval — vector search → LLM
- English-only reranker (ms-marco-MiniLM-L-6-v2)
- Ollama embedding model (nomic-embed-text-v2-moe)
- No query expansion — English query embedded as-is
- Result: good English queries, poor cross-lingual

**v2 (current development):**
- LLM query expansion before embedding
- Static XL_TERMS dictionary as fallback expansion
- Upgraded to multilingual bge-m3 embeddings
  (1024-dim) and bge-reranker-v2-m3 cross-encoder
- Taxonomy dual-query for broad questions
- Second retrieval pass when reranker confidence
  is below threshold
- RAG Insight panel, compare mode, model selector
- Result: stable 7.5–8/10 on independent legal
  expert evaluation; cross-lingual queries working

The regression (6/10 → 3.5/10) happened during
the v1→v2 migration when the reranker was
temporarily swapped to an English-only model.
Full root cause and recovery documented in the
learning journal.

---

## Ideas for where this could go

*These are early-stage ideas, not commitments.
Sharing them because the architecture is
interesting and feedback is welcome.*

**User document layer:**

A second RAG that reads the user's own documents
— employment contract, passport, qualification
certificates, rental agreement — and extracts
the facts of their specific situation. Combined
with the immigration law brain, an orchestration
agent could:

1. Read the user's documents and extract their
   profile (nationality, employment status,
   family situation, current residence status)
2. Identify which immigration requirements apply
   to their specific situation
3. Cross-reference what they have against what
   is required — identify gaps and risks
4. Produce structured output: what you have,
   what you need, what the risks are, what to
   do next

This would mirror what an immigration consultant
does in an initial assessment — read your
documents, know the law, tell you where you
stand. Entirely on-premise.

**Remaining known improvements to build:**

- §-level metadata filtering — query only
  FreizügG/EU without AufenthG chunks appearing
- Persist conversation history to a local file
  across browser sessions
- Extend source panel beyond 400-character
  truncation limit
- Strip LLM expansion echo (some models repeat
  the question instead of expanding it)

---

## Learning journal

This was built by someone with no prior AI
engineering background, learning in public.
The full write-up — every decision made, what
broke, the 3.5/10 regression and how it was
fixed, what was learned — is in docs/.

Honest documentation of failure is as important
as documentation of success.

[Read the learning journal →](./docs/Immigration_RAG_Learning_Journal.pdf)

---

## Feedback and collaboration

Comments, corrections, and ideas are genuinely
welcome — whether you are working in immigration
law, HR, legal tech, or AI engineering.

If you spot a legal error, a retrieval failure,
an architectural improvement, or have thoughts
on the document layer idea — please open an
issue or get in touch directly.

📧 arnavray@gmail.com

---

## Development process

**System architecture and product decisions:**

Arnav designed the core architecture and product
strategy for this system:

- Two-pass RAG pipeline (retrieve → rerank →
  generate) — the key architectural decision
  that separates answer quality from naive
  single-pass retrieval
- §-boundary chunking strategy — one § per
  chunk, ensuring no legal condition is ever
  split across retrieval nodes; designed the
  regex patterns and overflow-split logic
  to handle §§ exceeding token limits
- § metadata priority system — retrieval
  boosting for explicitly named §§, ensuring
  direct queries bypass cosine similarity and
  surface the right node first
- LLM query expansion design — English queries
  translated to German legal terms before
  embedding; fallback chain for expansion failure
- Legal corpus scope — AufenthG, FreizügG/EU,
  and BeschV selected with explicit rationale;
  StAG and AsylG deliberately excluded and
  disclosed to users
- On-premise privacy architecture — GDPR,
  data sovereignty, and professional liability
  rationale defined before any code was written
- Conversation memory design — 6-turn history
  window balancing follow-up awareness against
  context-length cost
- Model evaluation and selection — tested
  Mistral NeMo 12B vs Qwen 2.5 14B; defined
  the trade-off criteria (VRAM vs reasoning
  quality vs EU model provenance)
- Second retrieval pass threshold — defined
  the 0.1 reranker confidence floor below
  which retrieval reruns rather than generating
  from a low-confidence candidate set

**Testing and evaluation:**

Intensive testing and evaluation conducted by
Arnav, including:

- Independent legal expert scoring (external
  qualified reviewer, not self-assessed)
- Per-query evaluation with documented scores
  (8/10, 7.5/10) across four representative
  query classes
- A documented regression from 6/10 to 3.5/10,
  full root cause analysis, and verified
  recovery — included in the learning journal
  as an honest record of failure
- Iterative system prompt refinement across
  multiple evaluation rounds until legal
  accuracy stabilised
- Three-query regression test suite run after
  every architectural change

**Code implementation:**

Code generated with
[Claude Code](https://claude.ai/claude-code),
Anthropic's AI coding assistant.

---

## Disclaimer

Educational project and technical demonstration.
Outputs have not been verified by qualified legal
professionals and must not be relied upon for
real immigration or legal decisions. Always
consult a qualified immigration lawyer for your
specific situation.

---

## Licence

MIT — code only.
Legal corpus from gesetze-im-internet.de —
German federal law, public domain.
