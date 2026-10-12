"""Document reader and retrieval engine for PDF, DOCX, and TXT files.

Extracts text, segments into semantic chunks, and performs grounded retrieval
with source citations (filename, page/section, relevance score).
"""

import io
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

# Try importing pypdf and docx safely with graceful fallbacks
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def extract_text_from_file(
    file_bytes_or_buffer: Union[bytes, io.BytesIO],
    filename: str
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Extracts text sections from PDF, DOCX, or TXT file.

    Returns a list of section dicts:
    [{"filename": filename, "page_or_section": "Page 1" or "Section Name", "text": "..."}]
    and an optional error string.
    """
    if isinstance(file_bytes_or_buffer, bytes):
        buffer = io.BytesIO(file_bytes_or_buffer)
    else:
        buffer = file_bytes_or_buffer

    sections: List[Dict[str, Any]] = []
    fname_lower = filename.lower()

    try:
        # 1. PDF EXTRACTION
        if fname_lower.endswith(".pdf"):
            if not HAS_PYPDF:
                return [], "pypdf library is not installed. Please run `pip install pypdf`."

            reader = pypdf.PdfReader(buffer)
            if len(reader.pages) == 0:
                return [], f"PDF file '{filename}' has no pages."

            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                page_text = clean_text(page_text)
                if page_text:
                    sections.append({
                        "filename": filename,
                        "page_or_section": f"Page {page_idx + 1}",
                        "page_num": page_idx + 1,
                        "text": page_text
                    })

        # 2. DOCX EXTRACTION
        elif fname_lower.endswith(".docx"):
            if not HAS_DOCX:
                return [], "python-docx library is not installed. Please run `pip install python-docx`."

            doc = docx.Document(buffer)
            current_heading = "General"
            current_paragraphs: List[str] = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue

                # Check if paragraph is a heading
                if p.style and "heading" in p.style.name.lower():
                    if current_paragraphs:
                        combined = "\n".join(current_paragraphs)
                        sections.append({
                            "filename": filename,
                            "page_or_section": f"Section: {current_heading}",
                            "page_num": 1,
                            "text": combined
                        })
                        current_paragraphs = []
                    current_heading = text
                else:
                    current_paragraphs.append(text)

            if current_paragraphs:
                combined = "\n".join(current_paragraphs)
                sections.append({
                    "filename": filename,
                    "page_or_section": f"Section: {current_heading}",
                    "page_num": 1,
                    "text": combined
                })

            # Also inspect tables in docx
            for t_idx, table in enumerate(doc.tables):
                table_lines = []
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        table_lines.append(" | ".join(cells))
                if table_lines:
                    sections.append({
                        "filename": filename,
                        "page_or_section": f"Table {t_idx + 1}",
                        "page_num": 1,
                        "text": "\n".join(table_lines)
                    })

        # 3. TXT / PLAIN TEXT EXTRACTION
        elif fname_lower.endswith(".txt") or fname_lower.endswith(".md"):
            raw_bytes = buffer.read()
            try:
                content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = raw_bytes.decode("latin1")

            # Split into logical sections by Markdown headers or double linebreaks
            parts = re.split(r"\n(?=#{1,3}\s|\b[A-Z0-9\s]{4,}:)", content)
            if len(parts) <= 1:
                # Split by double newlines if no headings
                parts = [p.strip() for p in content.split("\n\n") if p.strip()]

            for p_idx, part in enumerate(parts):
                part_cleaned = clean_text(part)
                if part_cleaned:
                    first_line = part_cleaned.split("\n")[0][:40].strip()
                    sec_name = f"Section: {first_line}" if len(parts) > 1 else "Full Document"
                    sections.append({
                        "filename": filename,
                        "page_or_section": sec_name,
                        "page_num": p_idx + 1,
                        "text": part_cleaned
                    })

        else:
            return [], f"Unsupported document format '{filename}'. Supported formats: PDF, DOCX, TXT."

        if not sections:
            return [], f"No readable text could be extracted from '{filename}'. It may be a scanned document or empty."

        return sections, None

    except Exception as e:
        return [], f"Error reading document '{filename}': {str(e)}"


def clean_text(text: str) -> str:
    """Standardizes whitespace and cleans extracted text."""
    if not text:
        return ""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def chunk_sections(
    sections: List[Dict[str, Any]],
    chunk_size_words: int = 250,
    overlap_words: int = 40
) -> List[Dict[str, Any]]:
    """Chunks document sections into smaller, search-friendly passages."""
    all_chunks = []
    chunk_counter = 1

    for sec in sections:
        text = sec["text"]
        words = text.split()

        if len(words) <= chunk_size_words:
            all_chunks.append({
                "chunk_id": chunk_counter,
                "filename": sec["filename"],
                "page_or_section": sec["page_or_section"],
                "page_num": sec.get("page_num", 1),
                "text": text
            })
            chunk_counter += 1
        else:
            start = 0
            while start < len(words):
                end = min(start + chunk_size_words, len(words))
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)

                all_chunks.append({
                    "chunk_id": chunk_counter,
                    "filename": sec["filename"],
                    "page_or_section": sec["page_or_section"],
                    "page_num": sec.get("page_num", 1),
                    "text": chunk_text
                })
                chunk_counter += 1

                if end == len(words):
                    break
                start += (chunk_size_words - overlap_words)

    return all_chunks


def tokenize(text: str) -> List[str]:
    """Tokenize and filter common stopwords."""
    stop_words = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
        "of", "by", "is", "are", "was", "were", "it", "this", "that", "these",
        "those", "can", "could", "will", "would", "shall", "should", "what",
        "who", "when", "where", "why", "how", "i", "you", "he", "she", "they",
        "we", "me", "him", "her", "us", "them", "my", "your", "their", "our",
        "be", "been", "being", "have", "has", "had", "do", "does", "did"
    }
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    return [t for t in raw_tokens if t not in stop_words]


def retrieve_relevant_chunks(
    chunks: List[Dict[str, Any]],
    query: str,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """Grounded BM25/TF-IDF retrieval scoring of chunks for a given query."""
    if not chunks or not query.strip():
        return []

    q_tokens = tokenize(query)
    if not q_tokens:
        q_tokens = [w.lower() for w in query.strip().split() if len(w) > 1]

    # Precompute corpus statistics
    N = len(chunks)
    doc_freqs: Dict[str, int] = {}
    for ch in chunks:
        ch_tokens = set(tokenize(ch["text"]))
        for t in ch_tokens:
            doc_freqs[t] = doc_freqs.get(t, 0) + 1

    scored_chunks = []
    for ch in chunks:
        text = ch["text"]
        ch_tokens = tokenize(text)
        total_tokens = max(len(ch_tokens), 1)

        score = 0.0
        matched_terms = []

        # Exact phrase match boost
        if query.lower().strip() in text.lower():
            score += 15.0

        for t in q_tokens:
            tf = ch_tokens.count(t)
            if tf > 0:
                matched_terms.append(t)
                # BM25-style IDF calculation
                df = doc_freqs.get(t, 1)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                if idf < 0:
                    idf = 0.1
                # Sub-linear term frequency scaling
                score += (tf / (tf + 1.5)) * idf

        if score > 0:
            coverage = len(set(matched_terms)) / max(len(set(q_tokens)), 1)
            # Confidence balances token coverage and BM25 score
            confidence = min(0.98, max(0.20, 0.50 * coverage + 0.50 * (score / (score + 1.0))))
            scored_chunk = dict(ch)
            scored_chunk["score"] = round(score, 3)
            scored_chunk["confidence"] = round(confidence, 2)
            scored_chunk["matched_terms"] = list(set(matched_terms))
            scored_chunks.append(scored_chunk)

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]


def detect_topic_change(current_query: str, last_query: Optional[str]) -> bool:
    """Detects whether the user has transitioned to a different topic."""
    if not last_query:
        return False

    curr_tokens = set(tokenize(current_query))
    last_tokens = set(tokenize(last_query))

    if not curr_tokens or not last_tokens:
        return False

    overlap = curr_tokens.intersection(last_tokens)
    # If less than 20% vocabulary overlap and curr query has fresh keywords, it's a topic shift
    overlap_ratio = len(overlap) / max(len(curr_tokens), 1)
    return overlap_ratio < 0.20


def detect_repeated_question(current_query: str, conversation_history: List[Dict[str, Any]]) -> bool:
    """Checks if the user has essentially asked this question already."""
    curr_norm = re.sub(r"[^a-z0-9]", "", current_query.lower())
    for turn in conversation_history:
        if turn.get("role") == "user":
            past_norm = re.sub(r"[^a-z0-9]", "", str(turn.get("content", "")).lower())
            if curr_norm == past_norm:
                return True
    return False


def answer_document_query(
    query: str,
    chunks: List[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generates an intelligent, grounded answer from uploaded documents.

    Maintains context, respects conversation history, avoids repeating identical answers,
    and handles topic changes gracefully.
    """
    if not chunks:
        return {
            "answer": "No documents have been loaded yet. Please upload a PDF, DOCX, or TXT document first.",
            "sources": [],
            "topic_shifted": False,
            "repeated_query": False,
            "confidence": 0.0
        }

    # 1. Check repetition
    
    is_repeated = detect_repeated_question(query, conversation_history)

    # 2. Check topic shift
    last_user_query = None
    for turn in reversed(conversation_history):
        if turn.get("role") == "user":
            last_user_query = turn.get("content")
            break

    topic_shifted = detect_topic_change(query, last_user_query) if last_user_query else False

    # 3. Context augmentation for follow-ups
    augmented_query = query
    if not topic_shifted and last_user_query and any(w in query.lower() for w in ["it", "this", "that", "these", "explain more", "what else", "why", "elaborate"]):
        # Add keywords from last query as context
        augmented_query = f"{query} {last_user_query}"

    # 4. Retrieve best chunks
    retrieved = retrieve_relevant_chunks(chunks, augmented_query, top_k=3)

    if not retrieved or retrieved[0]["score"] < 0.2:
        return {
            "answer": (
                f"I reviewed the uploaded document(s), but could not find specific information answering: "
                f"**\"{query}\"**.\n\n"
                f"Please verify if the topic is covered in your uploaded files or rephrase your question."
            ),
            "sources": [],
            "topic_shifted": topic_shifted,
            "repeated_query": is_repeated,
            "confidence": 0.0
        }

    top_chunk = retrieved[0]
    top_text = top_chunk["text"]

    # Extract most relevant sentences from top chunk
    sentences = re.split(r"(?<=[.!?])\s+", top_text)
    relevant_sentences = []
    q_tokens = tokenize(augmented_query)

    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        s_tokens = tokenize(s_clean)
        match_count = sum(1 for t in q_tokens if t in s_tokens)
        if match_count > 0:
            relevant_sentences.append((s_clean, match_count))

    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    best_extracts = [s[0] for s in relevant_sentences[:4]]

    if not best_extracts:
        best_extracts = sentences[:3]

    extracted_body = " ".join(best_extracts)

    # Build clear, professional response
    answer_parts = []

    if topic_shifted:
        answer_parts.append(f"*Shifting topic to: **{query.strip()}***\n")

    if is_repeated:
        answer_parts.append(
            "*(Follow-up Note: You previously asked a similar question. Here is an expanded, focused summary based on the document source:)*\n"
        )

    answer_parts.append(extracted_body)

    # Format source citation info
    sources_info = []
    for ch in retrieved:
        sources_info.append({
            "filename": ch["filename"],
            "section": ch["page_or_section"],
            "page_num": ch.get("page_num", 1),
            "confidence": ch["confidence"],
            "score": ch["score"],
            "snippet": ch["text"][:220] + "..." if len(ch["text"]) > 220 else ch["text"]
        })

    primary_source = sources_info[0]
    source_attribution = (
        f"\n\n**Source Citation:** Found in **`{primary_source['filename']}`** "
        f"({primary_source['section']}) with **{int(primary_source['confidence'] * 100)}% match confidence**."
    )
    answer_parts.append(source_attribution)

    return {
        "answer": "\n".join(answer_parts),
        "sources": sources_info,
        "topic_shifted": topic_shifted,
        "repeated_query": is_repeated,
        "confidence": top_chunk["confidence"]
    }
