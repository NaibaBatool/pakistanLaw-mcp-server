"""Document search tool for querying the Pakistani legal document repository."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents"


def _get_corpus_files() -> list[Path]:
    """Retrieve all JSON or text files in the documents folder."""
    custom_dir = os.getenv("LEGAL_DOCS_DIR")
    if custom_dir:
        base_dir = Path(custom_dir)
        if not base_dir.is_absolute():
            base_dir = Path.cwd() / custom_dir
    else:
        base_dir = DOCS_DIR
        if not base_dir.exists():
            base_dir = Path.cwd() / "data" / "documents"

    if not base_dir.exists():
        return []
    return list(base_dir.glob("*.json")) + list(base_dir.glob("*.txt")) + list(base_dir.glob("*.md"))


def document_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search legal documents and retrieve relevant passages.

    Args:
        query: The question or subject to search for.
        max_results: Optional maximum number of passages to return (1-10).

    Returns:
        Dictionary with matching document passages, source types, and citations.
    """
    # 1. Input validation
    if not isinstance(query, str) or not query.strip():
        return {
            "query": query,
            "passages": [],
            "count": 0,
            "status": "error",
            "error_message": "Query must be a non-empty string.",
        }

    clean_query = query.strip()
    if len(clean_query) > 500:
        return {
            "query": clean_query[:50] + "...",
            "passages": [],
            "count": 0,
            "status": "error",
            "error_message": "Query length exceeds maximum limit of 500 characters.",
        }

    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 5
    max_results = max(1, min(max_results, 10))

    files = _get_corpus_files()
    if not files:
        return {
            "query": clean_query,
            "passages": [],
            "count": 0,
            "status": "empty_corpus",
            "explanation": (
                "No legal document collection is configured or the documents directory is empty. "
                "Add verified JSON/Markdown statute files to 'data/documents/' to enable local retrieval."
            ),
        }

    STOP_WORDS = {
        "what", "does", "of", "the", "in", "to", "a", "an", "is", "for", "and", "or",
        "section", "article", "act", "law", "state", "tell", "me", "about", "how",
        "can", "it", "its", "by", "on", "at", "with", "from", "as", "be", "this", "that"
    }
    raw_tokens = set(re.findall(r"\w+", clean_query.lower()))
    q_tokens = {t for t in raw_tokens if t not in STOP_WORDS}
    if not q_tokens:
        q_tokens = raw_tokens
    scored_passages: list[tuple[float, dict[str, Any]]] = []

    for filepath in files:
        if filepath.suffix.lower() == ".json":
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                continue

            doc_title = doc.get("title", filepath.stem)
            source_type = doc.get("source_type", "legislation")
            source_url = doc.get("source_url", "")
            pub_date = doc.get("publication_date", "")

            sections = doc.get("sections", [])
            for sec in sections:
                sec_num = str(sec.get("section_number", ""))
                sec_heading = sec.get("heading", "")
                sec_text = sec.get("text", "")
                keywords = sec.get("keywords", [])

                full_passage_text = f"Section {sec_num}: {sec_heading}\n{sec_text}"
                passage_tokens = set(re.findall(r"\w+", full_passage_text.lower()))

                overlap = len(q_tokens.intersection(passage_tokens))
                kw_overlap = sum(3 for kw in keywords if kw.lower() in clean_query.lower())
                total_score = overlap + kw_overlap

                if total_score > 0:
                    scored_passages.append((
                        total_score,
                        {
                            "document_title": doc_title,
                            "section": f"Section {sec_num} ({sec_heading})",
                            "passage": sec_text,
                            "source_type": source_type,
                            "source_url": source_url,
                            "publication_date": pub_date,
                            "score": total_score,
                        },
                    ))

        elif filepath.suffix.lower() in [".txt", ".md"]:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for p in paragraphs:
                p_tokens = set(re.findall(r"\w+", p.lower()))
                overlap = len(q_tokens.intersection(p_tokens))
                if overlap > 0:
                    scored_passages.append((
                        overlap,
                        {
                            "document_title": filepath.name,
                            "section": "Excerpt",
                            "passage": p,
                            "source_type": "official_notice" if "gazette" in filepath.name.lower() else "legislation",
                            "source_url": f"local://data/documents/{filepath.name}",
                            "publication_date": "",
                            "score": overlap,
                        },
                    ))

    scored_passages.sort(key=lambda x: x[0], reverse=True)
    results = [item[1] for item in scored_passages[:max_results]]

    if not results:
        return {
            "query": clean_query,
            "passages": [],
            "count": 0,
            "status": "not_found",
            "explanation": (
                f"No matching legal passages found in the configured repository for query '{clean_query}'. "
                "Consider refining your keywords or checking specific act names."
            ),
        }

    return {
        "query": clean_query,
        "passages": results,
        "count": len(results),
        "status": "success",
    }
