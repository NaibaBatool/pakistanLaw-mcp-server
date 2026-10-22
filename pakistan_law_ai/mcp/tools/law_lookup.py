"""Law lookup tool for retrieving verified Pakistani statutory provisions."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# Default directory for verified documents
DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents"


def _get_corpus_files() -> list[Path]:
    """Retrieve all JSON document files from the legal documents directory."""
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
    return list(base_dir.glob("*.json"))


def _extract_section_number(query: str) -> str | None:
    """Extract section or article number patterns like 'Section 21', 'Sec 154', 'Article 19'."""
    pattern = r"(?:section|sec\.?|article|art\.?)\s*([0-9]+[a-zA-Z]?(?:\([a-zA-Z0-9]+\))?)"
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def law_lookup(query: str, jurisdiction: str = "Pakistan") -> dict[str, Any]:
    """Retrieve specific laws, acts, sections, legal provisions, or references.

    Args:
        query: A law name, act, section, provision, or legal topic.
        jurisdiction: Jurisdiction filter, defaulting to 'Pakistan'.

    Returns:
        Dictionary containing verified statutory details, text extracts, and citations.
    """
    # 1. Input validation
    if not isinstance(query, str) or not query.strip():
        return {
            "query": query,
            "law_name": "Unknown",
            "section": "None",
            "retrieved_text": "",
            "source_url": "",
            "verification_status": "unverified",
            "source_date": "",
            "jurisdiction": jurisdiction,
            "error_message": "Query must be a non-empty string.",
        }

    clean_query = query.strip()
    if len(clean_query) > 500:
        return {
            "query": clean_query[:50] + "...",
            "law_name": "Unknown",
            "section": "None",
            "retrieved_text": "",
            "source_url": "",
            "verification_status": "unverified",
            "source_date": "",
            "jurisdiction": jurisdiction,
            "error_message": "Query length exceeds maximum limit of 500 characters.",
        }

    files = _get_corpus_files()
    if not files:
        return {
            "query": clean_query,
            "law_name": "No Corpus Configured",
            "section": "None",
            "retrieved_text": "",
            "source_url": "https://pakistancode.gov.pk",
            "verification_status": "unverified",
            "source_date": "",
            "jurisdiction": jurisdiction,
            "error_message": "Legal documents collection directory is empty or missing.",
        }

    extracted_sec = _extract_section_number(clean_query)
    STOP_WORDS = {
        "what", "does", "of", "the", "in", "to", "a", "an", "is", "for", "and", "or",
        "section", "article", "act", "law", "state", "tell", "me", "about", "how",
        "can", "it", "its", "by", "on", "at", "with", "from", "as", "be", "this", "that"
    }
    raw_tokens = set(re.findall(r"\w+", clean_query.lower()))
    q_tokens = {t for t in raw_tokens if t not in STOP_WORDS}
    if not q_tokens:
        q_tokens = raw_tokens

    best_match: dict[str, Any] | None = None
    best_score = -1

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            continue

        doc_title = doc.get("title", "")
        doc_short = doc.get("short_title", "")
        doc_jurisdiction = doc.get("jurisdiction", "Pakistan")
        doc_url = doc.get("source_url", "")
        pub_date = doc.get("publication_date", "")

        # Check jurisdiction compatibility
        if jurisdiction.lower() not in ["pakistan", "federal", "any"]:
            if jurisdiction.lower() not in doc_jurisdiction.lower():
                continue

        doc_text_score = 0
        doc_tokens = set(re.findall(r"\w+", (doc_title + " " + doc_short).lower()))
        common_doc = len(q_tokens.intersection(doc_tokens))
        doc_text_score += common_doc * 3

        sections = doc.get("sections", [])
        for sec in sections:
            sec_num = str(sec.get("section_number", "")).strip().lower()
            clean_sec_num = sec_num.replace("article", "").replace("sec", "").strip()

            # If user explicitly asked for a section/article number, strictly enforce section match
            if extracted_sec:
                matches_section = (
                    extracted_sec == sec_num
                    or extracted_sec == clean_sec_num
                    or f"({extracted_sec})" in sec_num
                    or f" {extracted_sec}" in sec_num
                )
                if not matches_section:
                    continue  # Do not match unrelated sections when user asked for a specific section

            sec_heading = sec.get("heading", "")
            sec_text = sec.get("text", "")
            keywords = sec.get("keywords", [])

            score = doc_text_score
            if extracted_sec:
                score += 50

            # Keyword and text matching
            sec_tokens = set(re.findall(r"\w+", (sec_heading + " " + sec_text + " " + " ".join(keywords)).lower()))
            overlap = len(q_tokens.intersection(sec_tokens))
            score += overlap * 2

            for kw in keywords:
                if kw.lower() in clean_query.lower():
                    score += 5

            if score > best_score:
                best_score = score
                best_match = {
                    "query": clean_query,
                    "law_name": doc_title,
                    "short_title": doc_short,
                    "section": f"Section / Article {sec.get('section_number')}: {sec_heading}",
                    "retrieved_text": sec_text,
                    "source_url": doc_url,
                    "verification_status": doc.get("verification_status", "verified_statute"),
                    "source_date": pub_date,
                    "jurisdiction": doc_jurisdiction,
                    "relevance_score": score,
                    "notes": (
                        "Verified text extracted directly from official legislative records (Pakistan Code). "
                        "Subject to provincial adaptations or subsequent gazette amendments where applicable."
                    ),
                }

    if best_match and best_score >= 4:
        return best_match

    return {
        "query": clean_query,
        "law_name": "Unverified / Not Found in Corpus",
        "section": "None",
        "retrieved_text": (
            "No verified Pakistani statutory provision matching this query could be found in the current "
            "authoritative local repository. Please check section numbers or consult the official Pakistan "
            "Code directly at https://pakistancode.gov.pk."
        ),
        "source_url": "https://pakistancode.gov.pk",
        "verification_status": "unverified",
        "source_date": "",
        "jurisdiction": jurisdiction,
        "notes": "Provision could not be verified against the local official corpus.",
    }
