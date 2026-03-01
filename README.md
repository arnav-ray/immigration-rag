---

# German Immigration Law RAG

A local-first Retrieval-Augmented Generation (RAG)
system for querying German immigration law in English
and German. Built as a learning project — not an
expert system. The full learning journal is in
docs/.

---

## Demo

*Add demo.mp4 to the demo/ folder*

---

## What it does

Ask questions about German immigration law in English
or German. The system finds the relevant legal § ,
quotes the exact German text, and explains it in
plain language. Every answer cites the specific §
it drew from.

**Example queries:**
- What is the Blue Card EU and who qualifies?
- What rights do EU citizens have when moving to Germany?
- Can my non-EU spouse join me in Germany as an EU citizen?
- What residence permit does a non-EU spouse of a German citizen get?

---

## Legal corpus

Three laws, all sourced from
[gesetze-im-internet.de](https://www.gesetze-im-internet.de):

| Law | Applies to | Chunks |
|-----|-----------|--------|
| AufenthG | Non-EU nationals | 197 |
| FreizügG/EU | EU citizens and family members | 23 |
| BeschV | Work permit approvals | 48 |

---

## Architecture
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
qwen2.5:14b — answer generated from reranked top 5
↓
Cited answer + source panel

**Key design decisions:**

- **Two-pass pipeline**: retrieve 20 → rerank →
  generate. Reranker affects the answer, not just
  the display panel.
- **Structural chunker**: splits on Markdown §
  headers. One complete § per node. Never splits
  a legal condition across chunks.
- **§ metadata priority**: if the user names a §
  explicitly, that chunk is prioritised before
  the reranker runs.
- **Law metadata**: every chunk tagged with source
  law and § number at index time.
- **Local-only**: Ollama runs everything on GPU.
  Zero data leaves the machine.

---

## Stack

| Component | Choice |
|-----------|--------|
| LLM | qwen2.5:14b via Ollama |
| Embeddings | nomic-embed-text-v2-moe |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Framework | LlamaIndex |
| Vector store | LlamaIndex JSON flat-file |
| UI | Streamlit |

---

## Independent legal evaluation

Evaluated by an external legal expert across
multiple iterations:

| Query | Score | Notes |
|-------|-------|-------|
| EU citizen rights | 6/10 → 3.5/10 → 7/10 | Regression documented in learning journal |
| Blue Card salary | 8/10 | Final state |
| EU citizen rights | 7.5/10 | Final state |
| Non-EU spouse of EU citizen | 8/10 | Final state |
| Non-EU spouse of German citizen | 7.5/10 | Was 2/10 before reranker fix |

The regression from 6/10 to 3.5/10 and its root
cause are documented in the learning journal.
Showing what broke is as important as showing
what works.

---

## How to run

**Requirements:**
- NVIDIA GPU with 8GB+ VRAM
- Ollama installed — [ollama.ai](https://ollama.ai)
- Python 3.11+
- Run on mains power (battery throttling causes
  timeout errors at this context window size)

**Setup:**
```bash
# 1. Pull models
ollama pull qwen2.5:14b
ollama pull nomic-embed-text-v2-moe

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download laws from gesetze-im-internet.de
#    AufenthG, FreizügG/EU, BeschV as HTML
#    Convert to Markdown using Docling:
pip install docling
#    Place converted .md files in data_output/

# 4. Build the vector index
python build_db.py

# 5. Run
streamlit run app.py
```

---

## Known limitations

- Citizenship and naturalisation questions require
  StAG which is not in this corpus. The system
  states this explicitly when asked.
- Asylum law (AsylG) and social benefits law (SGB)
  are out of scope.
- The system prompt in this repository is a
  functional stub. The production prompt was
  developed through iterative external legal
  evaluation and is not included.
- Run on mains power. Battery power causes GPU
  throttling and timeout errors.

---

## Learning journal

Full write-up of what was built, what broke,
and what was learned — including the 3.5/10
regression, its root cause, and how it was fixed:

[docs/Immigration_RAG_Learning_Journal.pdf](./docs/Immigration_RAG_Learning_Journal.pdf)

---

## Licence

MIT — code only.
Legal corpus sourced from gesetze-im-internet.de
(German federal law — public domain).

---

## Disclaimer

Educational project and technical demonstration.
Outputs have not been verified by qualified legal
professionals. Do not rely on this tool for real
immigration or legal decisions.
