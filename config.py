"""
Central configuration for the immigration-rag application.

All tuneable values live here so no model name, path, or threshold
is scattered across multiple source files.  Values can be overridden
via environment variables (see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present; silently skips if absent

# ── LLM ────────────────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:14b")
LLM_REQUEST_TIMEOUT: float = float(os.getenv("LLM_REQUEST_TIMEOUT", "300.0"))
LLM_NUM_CTX: int = int(os.getenv("LLM_NUM_CTX", "8192"))

# ── Embedding model ─────────────────────────────────────────────────────────────
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text-v2-moe")

# Build-time LLM (used by build_db.py — lighter model for offline indexing)
BUILD_LLM_MODEL: str = os.getenv("BUILD_LLM_MODEL", "mistral-nemo:12b")
BUILD_LLM_TIMEOUT: float = float(os.getenv("BUILD_LLM_TIMEOUT", "120.0"))
BUILD_LLM_NUM_CTX: int = int(os.getenv("BUILD_LLM_NUM_CTX", "16384"))

# ── Reranker ────────────────────────────────────────────────────────────────────
RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANKER_MAX_LEN: int = int(os.getenv("RERANKER_MAX_LEN", "512"))

# ── Retrieval ───────────────────────────────────────────────────────────────────
RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "20"))
RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", "5"))

# ── Paths ───────────────────────────────────────────────────────────────────────
PERSIST_DIR: str = os.getenv("PERSIST_DIR", "./data_vector_store")
DATA_INPUT_DIR: str = os.getenv("DATA_INPUT_DIR", "data_input")
DATA_OUTPUT_DIR: str = os.getenv("DATA_OUTPUT_DIR", "data_output")

# ── Input safety ────────────────────────────────────────────────────────────────
MAX_QUERY_LEN: int = int(os.getenv("MAX_QUERY_LEN", "2000"))
MAX_HISTORY_TURN_LEN: int = int(os.getenv("MAX_HISTORY_TURN_LEN", "4000"))
MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "6"))

# ── Document ingestion ──────────────────────────────────────────────────────────
ALLOWED_INGEST_EXTENSIONS: set = {".pdf", ".html", ".docx", ".md", ".txt"}

# ── Logging ─────────────────────────────────────────────────────────────────────
LOG_FILE: str = os.getenv("LOG_FILE", "rag_audit.log")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
