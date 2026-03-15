---
name: german-immigration-rag
description: Local RAG assistant for German immigration law (AufenthG, FreizügG/EU, BeschV). Use when user asks about German residence permits, visa types, Blue Card, Opportunity Card, skilled worker rules, EU free movement, family reunification, or tolerated stay — answers retrieved directly from indexed German legal text. Also use when a developer asks to set up, rebuild, test, or debug the local RAG system. Trigger phrases include: "Blue Card", "Blaue Karte", "Niederlassungserlaubnis", "Chancenkarte", "Familiennachzug", "AufenthG", "FreizügG", "residence permit", "skilled worker Germany", "rebuild index", "vector store".
compatibility: Python 3.11+, LlamaIndex, Streamlit. Embeddings via HuggingFace (BAAI/bge-m3, auto-downloaded ~1.2 GB). Reranker via HuggingFace (BAAI/bge-reranker-v2-m3, auto-downloaded ~1.1 GB). LLM via Ollama — any model selectable in sidebar (qwen2.5:14b default). NVIDIA GPU strongly recommended.
metadata:
  author: Arnav Amal Ray
  version: 2.0.0
  category: legal-research
  tags: [german-law, immigration, rag, aufenthg, llamaindex, bge-m3]
---

# German Immigration Law RAG — Operator Guide

A local Retrieval-Augmented Generation system over German immigration law,
running entirely on-premise via Ollama. No data leaves the machine.

**Corpus:**

| Law | Applies to |
|-----|-----------|
| AufenthG (Aufenthaltsgesetz) | Third-country nationals — residence permits, visa, deportation |
| FreizügG/EU | EU/EEA citizens and family — free movement rights |
| BeschV (Beschäftigungsverordnung) | Employment permit approval — Federal Agency consent |

**Disclaimer:** Educational learning project. Outputs are AI-generated and
must not be taken as legal advice.

For full architecture and pipeline details, see `references/architecture.md`.
For authoritative EN↔DE legal term mapping, see `references/legal-terminology.md`.

---

## Step 1: Classify the User Before Answering

Every immigration question must be routed to the correct legal regime:

- EU/EEA citizen → **FreizügG/EU**
- Non-EU national (third-country) → **AufenthG**
- Employment permit approval question → **BeschV**
- Mixed case (e.g. non-EU spouse of EU citizen) → state which law
  governs each part explicitly before answering

Never mix AufenthG and FreizügG/EU rules in a single answer without
explicit regime separation. See `references/legal-terminology.md`
for the full regime routing table.

---

## Step 2: Translate English Terms to German Legal Terms

English queries must be mentally translated before retrieval. See
`references/legal-terminology.md` for the authoritative mapping.

Critical translations:

| English | German | § |
|---------|--------|---|
| Blue Card | Blaue Karte EU | § 18g AufenthG (NOT § 19a — outdated) |
| Opportunity Card | Chancenkarte | § 20a AufenthG |
| Settlement permit / Permanent residence | Niederlassungserlaubnis | § 9 AufenthG |
| Temporary residence permit | Aufenthaltserlaubnis | § 7 AufenthG |
| EU long-term residence | Erlaubnis zum Daueraufenthalt-EU | § 9a AufenthG |
| Family reunification | Familiennachzug | § 27–36 AufenthG |
| Skilled worker (degree) | Fachkraft mit akademischer Ausbildung | § 18b AufenthG |
| Tolerated stay | Duldung | § 60a AufenthG |
| Freedom of movement (EU) | Freizügigkeit | § 2 FreizügG/EU |

The LLM query expansion pipeline attempts this translation automatically.
If the wrong § is returned, name the § explicitly in your query.

---

## Step 3: Format Every Legal Answer Correctly

1. **State §§ first** — list only §§ that appear in retrieved context.
   Never cite §§ from memory.
2. **Quote German text** — reproduce the exact German in quotation marks.
3. **Explain in plain language** — immediately after the German quote.
4. **Match query language** — German question → German answer.
   English question → English answer.
5. **Never state salary thresholds in EUR** — the § text uses percentages
   of the Beitragsbemessungsgrenze, which changes annually.
6. **End with disclaimer** — *"Please verify the source text in the panel
   below before relying on this for any decision."*

---

## Setup: First-Time Installation

```bash
# 1. Pull an LLM via Ollama
ollama pull qwen2.5:14b

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download legal corpus from gesetze-im-internet.de (HTML format)
#    Place in data_input/, then run:
python ingest_pdf.py
# → produces structured Markdown files in data_output/

# 4. Build the vector index
python build_db.py
# → BAAI/bge-m3 (~1.2 GB) downloads automatically on first run
# → index saved to data_vector_store/

# 5. Launch the UI
streamlit run app.py
# → BAAI/bge-reranker-v2-m3 (~1.1 GB) downloads on first launch
# → opens at http://localhost:8501
```

**After any change to documents, embedding model, or chunking:**
1. Delete `data_vector_store/` directory
2. Re-run `python build_db.py`

---

## Developer Rebuild Checklist

After any document or model change, verify with these three queries:

1. `"Was ist eine Niederlassungserlaubnis und welche Voraussetzungen gelten?"` — German, structural
2. `"What is an Opportunity Card and who qualifies?"` — English, cross-lingual
3. `"§ 18g AufenthG — Blaue Karte EU Voraussetzungen"` — § direct lookup

If any query returns a hallucinated § or an empty source panel,
the rebuild is not complete.

---

## Examples

### Example 1: EU Citizen Residence Rights

User: *"Can I live in Germany as an EU citizen?"*

1. Classify: EU citizen → FreizügG/EU (not AufenthG)
2. Retrieve: § 2 Abs. 2 FreizügG/EU
3. Cover three phases:
   - First 3 months: no conditions
   - Beyond 3 months: must fall under § 2 Abs. 2 categories (worker, student, self-employed, self-sufficient)
   - Permanent residence after 5 years: § 4a FreizügG/EU
4. Answer in English

### Example 2: Blue Card Requirements

User: *"What are the Blue Card requirements?"*

1. Translate: "Blue Card" → `Blaue Karte EU` → § 18g AufenthG
   *(not § 18a = vocational, not § 19a = outdated 2023 reform)*
2. Retrieve chunks for § 18g
3. Quote German text, explain in English
4. Express salary threshold as % of Beitragsbemessungsgrenze — never EUR

### Example 3: Non-EU Spouse of EU Citizen

User: *"My husband is French and I am Indian. Can I join him in Germany?"*

1. Classify: Non-EU spouse of EU citizen → FreizügG/EU § 3
   *(direct family member — automatic derived right, not AufenthG)*
2. Note: No prior cohabitation required for direct family members
3. Retrieve: § 3 FreizügG/EU

### Example 4: Cross-Lingual Retrieval

User: *"What is a settlement permit?"*

1. Translate: "settlement permit" → `Niederlassungserlaubnis` → § 9 AufenthG
2. The LLM expansion pipeline generates these German terms automatically
3. If wrong § is returned: name § 9 explicitly in the query

---

## Troubleshooting

**Wrong § retrieved for a known permit type:**
- LLM expansion may have generated generic terms matching multiple §§
- Fix: name the § explicitly, or add the specific conditions (salary,
  qualification type, timeframe)

**LLM answers in German for an English question:**
- Language detection heuristic missed — query had no common English
  function words
- Fix: rephrase with words like "what", "how", "can", "does"

**RAG Insight shows all reranker scores near 0.0:**
- Old English-only reranker may be loaded from HuggingFace cache
- Fix: clear cache for `cross-encoder/ms-marco-MiniLM-L-6-v2`,
  restart app — `bge-reranker-v2-m3` will re-download

**`Database already exists` but results are stale:**
- Old vector store built with a different embedding model
- Fix: delete `data_vector_store/` directory, re-run `build_db.py`

**Ollama connection refused:**
- Ollama server not running
- Fix: run `ollama serve` in a separate terminal before starting the app

**Slow responses (over 60 seconds):**
- LLM running on CPU instead of GPU
- Fix: run `ollama ps` — should show GPU utilization. If CPU, check
  CUDA drivers and run on mains power (battery throttles GPU).

**System says it has no information on a topic:**
- Topic may be outside corpus scope (StAG, AsylG, SGB)
- This is correct behaviour — the system is designed to acknowledge
  gaps rather than hallucinate

---

## Critical Legal Accuracy Rules

- **Never cite a § not in the retrieved chunks.** A wrong § citation
  is worse than admitting uncertainty.
- **§ 18a is NOT the Blue Card.** § 18a = qualified professional
  (vocational training). Blue Card = § 18g.
- **§ 19a is outdated** — replaced by § 18g in the 2023
  Fachkräfteeinwanderungsgesetz reform. Do not cite § 19a as current.
- **§ 28 is not a standalone title** — it is a sub-category of
  Aufenthaltserlaubnis for family members of German citizens.
- **Erlaubnis zum Daueraufenthalt-EU (§ 9a) is for third-country
  nationals only.** EU citizens use § 4a FreizügG/EU — a different law.
- **Never state salary thresholds in EUR.** The § uses Beitragsbe-
  messungsgrenze percentages, which change each year.
