---
name: german-immigration-rag
description: Guides setup, operation, troubleshooting, and extension of the German Immigration Law RAG system. Use when user asks how to install or run the immigration law assistant, build or rebuild the vector database, configure or swap Ollama models, troubleshoot timeout or GPU errors, fix poor retrieval quality, or add new laws to the corpus.
metadata:
  author: Arnav
  version: 1.0.0
---

# German Immigration Law RAG — Operator Guide

An on-premise RAG pipeline answering questions about German immigration law
(AufenthG, FreizügG/EU, BeschV) via Ollama. No cloud API. No data leaves
the machine.

For full architecture details, see `references/architecture.md`.

---

## Step 1: Prerequisites

**Hardware**
- NVIDIA GPU with 8 GB+ VRAM
- Run on mains power — battery throttling causes GPU offloading and
  request timeout errors

**Software**
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running

**Pull the required models:**
```bash
ollama pull qwen2.5:14b
ollama pull nomic-embed-text-v2-moe
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

---

## Step 2: Prepare the Legal Corpus

1. Download the source HTML files from
   [gesetze-im-internet.de](https://www.gesetze-im-internet.de):
   - `AufenthG` (Aufenthaltsgesetz)
   - `FreizügG/EU` (Freizügigkeitsgesetz)
   - `BeschV` (Beschäftigungsverordnung)

2. Place the downloaded HTML files in `data_input/`

3. Run the ingestion script to convert to structured Markdown:
   ```bash
   python ingest_pdf.py
   ```
   Expected output: `.md` files in `data_output/`, one per law.

---

## Step 3: Build the Vector Database

```bash
python build_db.py
```

Expected output:
```
1. Waking up the AI Models...
2. Reading the structured Markdown files from 'data_output'...
3. Splitting on § headers, filtering noise, tagging metadata...
   Raw blocks : ~280
   Filtered   : ~12  (preamble + ToC noise)
   Overflow   : ~3   (extra sub-chunks from long §§)
   Final nodes: ~268
   AufenthG: 197 node(s)
   BeschV: 48 node(s)
   FreizügG/EU: 23 node(s)
4. Building vector index...
5. Saving Database to Hard Drive...
Success! Database physically saved to: data_vector_store
```

If you see `Database already exists at data_vector_store. Ready for UI!`,
the index was already built. Delete `data_vector_store/` to rebuild.

---

## Step 4: Run the Application

```bash
streamlit run app.py
```

The UI opens in your browser at `http://localhost:8501`.

**Example queries to test with:**
- *Was ist die Blaue Karte EU und wer ist berechtigt?*
- *What are the rules for a settlement permit for skilled workers?*
- *Welche Voraussetzungen gelten für den Familiennachzug?*

---

## Examples

### Scenario 1: First-time setup
User: "How do I get this running from scratch?"

Actions:
1. Confirm GPU VRAM ≥ 8 GB and Ollama is installed
2. Walk through Steps 1–4 in sequence
3. Verify final node count matches expected values
4. Run a test query to confirm retrieval

Result: Working assistant citing §§ with source panel

### Scenario 2: Rebuilding the database after corpus update
User: "I added a new law — how do I update the index?"

Actions:
1. Place new `.md` file in `data_output/`
2. Delete `data_vector_store/` directory
3. Run `python build_db.py` again
4. Confirm new law appears in the node count summary

Result: Expanded corpus with new law indexed and retrievable

### Scenario 3: Switching the LLM
User: "I want to try Mistral NeMo instead of Qwen."

Actions:
1. Run `ollama pull mistral-nemo:12b`
2. In `app.py`, line 50: change `"qwen2.5:14b"` to `"mistral-nemo:12b"`
3. Restart the Streamlit app
4. Note: Mistral NeMo has weaker multi-condition reasoning but uses
   less VRAM and is EU-jurisdiction by provenance

Result: App running with alternative model, no other changes needed

---

## Troubleshooting

### Error: Request timeout / ollama connection refused

**Cause:** Ollama is not running, or GPU is throttled (battery mode).

**Solution:**
1. Start Ollama: open the Ollama app or run `ollama serve`
2. Plug in mains power and retry
3. If still failing, increase timeout in `app.py` line 50:
   `request_timeout=300.0` → `request_timeout=600.0`

### Error: CUDA out of memory / model offloaded to CPU

**Cause:** VRAM insufficient for the 14B model.

**Solution:**
- Switch to `mistral-nemo:12b` (requires ~8 GB VRAM vs ~9 GB for 14B)
- Or reduce context window: in `app.py` line 50, change
  `"num_ctx": 8192` to `"num_ctx": 4096`

### Poor retrieval quality — wrong §§ returned

**Cause:** Query phrasing does not match § content, or reranker is not
filtering effectively.

**Solution:**
1. Try naming the § explicitly: "§ 18b requirements" instead of
   "Blue Card requirements" — the § priority boost fires on explicit
   references
2. Check the "View Local Law Sources" expander — if the right § appears
   in sources but the answer is wrong, the problem is generation not
   retrieval (adjust the system prompt in `app.py`)
3. If the right § is not in sources at all, the corpus may be missing
   that law — check node counts from `build_db.py`

### System answers "I don't have information on that"

**Cause:** Query is about a law not in the corpus (StAG, AsylG, SGB).

**Expected behaviour:** This is correct. The system is scoped to
AufenthG, FreizügG/EU, and BeschV only. It is designed to acknowledge
gaps rather than hallucinate.

**If the law should be covered:** rebuild the corpus with the additional
law (see Scenario 2 above).

### `data_vector_store` exists but app crashes on load

**Cause:** Index was built with a different embedding model than the one
currently configured.

**Solution:** Delete `data_vector_store/` and rebuild with
`python build_db.py`. Embedding model must match between build and
query time.

---

## Extending the Corpus

To add a new German law (e.g. StAG for citizenship):

1. Download the HTML from gesetze-im-internet.de
2. Place in `data_input/`
3. Run `python ingest_pdf.py` — adds a new `.md` to `data_output/`
4. Add a law tag in `build_db.py`, function `get_law_tag()`:
   ```python
   elif "stag" in name:
       return "StAG"
   ```
5. Delete `data_vector_store/` and rebuild
6. Update the system prompt in `app.py` to include the new law in the
   list of covered statutes

Note: The chunker splits on `## §` and `### §` headers. Verify the
converted Markdown uses those heading levels for § sections before
building the index.

For architecture details and chunking logic, see
`references/architecture.md`.
