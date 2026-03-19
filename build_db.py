import os
import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.schema import TextNode
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

import config

print("1. Waking up the AI Models...")
Settings.llm = Ollama(
    model=config.BUILD_LLM_MODEL,
    request_timeout=config.BUILD_LLM_TIMEOUT,
    additional_kwargs={"num_ctx": config.BUILD_LLM_NUM_CTX},
)
Settings.embed_model = OllamaEmbedding(
    model_name=config.EMBED_MODEL,
    text_instruction="search_document: ",
    query_instruction="search_query: ",
)

PERSIST_DIR = config.PERSIST_DIR

# ── Constants ──────────────────────────────────────────────────────────────────
# AufenthG uses ### for §§; FreizügG/EU and BeschV use ## for §§.
# Pattern matches any ##/###/#### header line that opens a § section.
SECTION_HEADER_RE = re.compile(r'^#{2,4}\s+§\s*\d+', re.MULTILINE)
SECTION_NUM_RE    = re.compile(r'§\s*(\d+[a-z]?)')
PREAMBLE_MARKERS  = ["Ausfertigungsdatum", "Vollzitat", "BGBl."]

OVERFLOW_CHARS = 10_000   # ~2,500 tokens × 4 chars/token — trigger threshold
SPLIT_TARGET   =  8_000   # ~2,000 tokens — aim to cut here, at nearest blank line

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_law_tag(filename: str) -> str:
    name = filename.lower()
    if "beschv" in name:
        return "BeschV"
    elif "freiz" in name:
        return "FreizügG/EU"
    return "AufenthG"


def is_noise_chunk(text: str) -> bool:
    """Return True for law-header preambles or table-of-contents blocks."""
    # Preamble: all three markers present together
    if all(marker in text for marker in PREAMBLE_MARKERS):
        return True
    # ToC: pipe characters dominate (Markdown table rows)
    non_empty = len(text) - text.count('\n') - text.count(' ')
    if non_empty > 0 and text.count('|') / len(text) > 0.05:
        return True
    return False


def extract_section(block: str) -> str:
    """
    Return a section label for this chunk:
    Step 1 — § number in the heading line (e.g. '§ 18g')
    Step 2 — cleaned heading text if no § number (e.g. 'Einleitung')
    Step 3 — § number anywhere in the full chunk text
    Step 4 — 'Vorbemerkung' (German legal term for unnumbered introductory content)
    """
    lines = block.splitlines()

    if lines:
        first = lines[0]

        # Step 1: § number in heading line
        m = SECTION_NUM_RE.search(first)
        if m:
            return f"§ {m.group(1)}"

        # Step 2: clean heading text — strip ## markers and (continued) prefix
        cleaned = re.sub(r'^#{2,4}\s*', '', first).strip()
        cleaned = re.sub(r'^\(continued\)\s*', '', cleaned).strip()
        if cleaned:
            return cleaned

    # Step 3: § reference anywhere in chunk
    m = SECTION_NUM_RE.search(block)
    if m:
        return f"§ {m.group(1)}"

    # Step 4
    return "Vorbemerkung"


def split_on_sections(text: str) -> list:
    """
    Split document text into one block per § heading.
    Returns the preamble block (if any) as the first item.
    Every block starting with a § header is one complete legal section.
    """
    matches = list(SECTION_HEADER_RE.finditer(text))
    if not matches:
        return [text]

    blocks = []
    # Preamble: everything before the first § header
    if matches[0].start() > 0:
        pre = text[:matches[0].start()]
        if pre.strip():
            blocks.append(pre)

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append(text[start:end])

    return blocks


def overflow_split(block: str) -> list:
    """
    Break a § block that exceeds OVERFLOW_CHARS at the nearest blank line
    after SPLIT_TARGET chars. Continued sub-chunks are prefixed with
    '(continued) <heading line>' so section metadata extraction still fires.
    """
    if len(block) <= OVERFLOW_CHARS:
        return [block]

    heading_line = block.splitlines()[0] if block.splitlines() else ""
    chunks = []
    remaining = block

    while len(remaining) > OVERFLOW_CHARS:
        # Find the nearest blank line after SPLIT_TARGET
        m = re.search(r'\n\s*\n', remaining[SPLIT_TARGET:])
        if m:
            cut = SPLIT_TARGET + m.start() + 1
        else:
            cut = SPLIT_TARGET  # no blank line found — hard cut

        chunks.append(remaining[:cut])
        remaining = f"(continued) {heading_line}\n\n" + remaining[cut:].lstrip()

    if remaining.strip():
        chunks.append(remaining)

    return chunks


# ── Main indexing pipeline ─────────────────────────────────────────────────────

if not os.path.exists(PERSIST_DIR):
    print("2. Reading the structured Markdown files from 'data_output'...")
    documents = SimpleDirectoryReader(input_dir=config.DATA_OUTPUT_DIR).load_data()

    print("3. Splitting on § headers, filtering noise, tagging metadata...")
    nodes = []
    raw_blocks = filtered_blocks = overflow_extra = 0

    for doc in documents:
        law = get_law_tag(doc.metadata.get("file_name", ""))
        blocks = split_on_sections(doc.text)
        raw_blocks += len(blocks)

        for block in blocks:
            # Change 1: discard preamble and ToC blocks
            if is_noise_chunk(block):
                filtered_blocks += 1
                continue

            # Change 3: overflow protection for very long § blocks
            sub_blocks = overflow_split(block)
            if len(sub_blocks) > 1:
                overflow_extra += len(sub_blocks) - 1

            for sub in sub_blocks:
                # Change 2: extract § number or heading as section metadata
                section = extract_section(sub)
                node = TextNode(
                    text=sub,
                    metadata={**doc.metadata, "law": law, "section": section},
                )
                nodes.append(node)

    print(f"   Raw blocks : {raw_blocks}")
    print(f"   Filtered   : {filtered_blocks}  (preamble + ToC noise)")
    print(f"   Overflow   : {overflow_extra}  (extra sub-chunks from long §§)")
    print(f"   Final nodes: {len(nodes)}")
    print()

    law_counts = {}
    for node in nodes:
        law = node.metadata["law"]
        law_counts[law] = law_counts.get(law, 0) + 1
    for law, count in sorted(law_counts.items()):
        print(f"   {law}: {count} node(s)")

    print("\n4. Building vector index...")
    index = VectorStoreIndex(nodes)

    print("5. Saving Database to Hard Drive...")
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    print(f"Success! Database physically saved to: {PERSIST_DIR}")

else:
    print(f"Database already exists at {PERSIST_DIR}. Ready for UI!")
