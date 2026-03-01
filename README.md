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
Zero data leaves the machine. No API keys.
No per-query costs. No terms-of-service
exposure.

---

## Why local models work for this

**Mistral NeMo 12B** (tested, functional):
- Built by Mistral AI — a French company,
  EU jurisdiction, EU data governance norms.
- 12B parameters fits in consumer GPU VRAM
  (8GB+).
- Strong multilingual capability via Tekken
  tokeniser — handles German legal text well.
- Suitable as a first-line on-premise assistant
  for legal or HR query work.
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
The pipeline is model-agnostic — swap the model
name in one line of app.py.

---

## What it does today

Ask questions about German immigration law in
English or German. The system retrieves the
relevant § from statute, quotes the exact German
legal text, and explains it in plain language.
Every answer cites the § it drew from. Users
can verify the source text directly in the
interface.

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
| AufenthG | Non-EU nationals | 197 |
| FreizügG/EU | EU citizens and family | 23 |
| BeschV | Work permit approvals | 48 |

---

## Technical architecture
```
User query
    ↓
nomic-embed-text-v2-moe (query embedding)
    ↓
Vector store — cosine similarity, k=20 candidates
    ↓
§ metadata priority — explicitly named §§ boosted
    ↓
Cross-encoder reranker — top 5 by true relevance
    ↓
qwen2.5:14b — answer from reranked top 5
    ↓
Cited answer + source panel
```

**Key decisions:**
- One § per chunk — structural Markdown chunker,
  never splits a legal condition across nodes
- Two-pass pipeline — retrieve then rerank then
  generate. Reranker affects the answer, not just
  the display.
- Law metadata on every chunk — enables §
  priority retrieval when user names a specific
  section
- Conversation memory — last 6 turns retained
  for follow-up questions

---

## How to run

**Requirements:** NVIDIA GPU 8GB+ VRAM,
[Ollama](https://ollama.ai), Python 3.11+.
Run on mains power — battery throttling causes
timeout errors.
```bash
# Pull models
ollama pull qwen2.5:14b
ollama pull nomic-embed-text-v2-moe

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

---

## Known limitations

- Citizenship and naturalisation require StAG —
  not in corpus. System states this explicitly
  when asked.
- Asylum law (AsylG) and social benefits (SGB)
  are out of scope.
- The system prompt in this repository is a
  functional stub. The production prompt was
  developed through iterative legal evaluation
  and is not included.
- Run on mains power. Battery throttling causes
  GPU offloading and timeout errors.

---

## Ideas for where this could go

*These are early-stage ideas, not commitments.
This is a learning project and roadmap items
may or may not get built. Sharing them publicly
because the architecture is interesting and
feedback is welcome.*

**User document layer (thinking about this):**

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
stand. Entirely on-premise. The user's documents
never leave their machine.

Whether this gets built depends on what is
learned from the current layer. Raising it here
because the architecture is worth discussing
even if the implementation is uncertain.

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
