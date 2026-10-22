"""Legal explanation tool for translating retrieved statutory context into plain language."""

from __future__ import annotations

import json
import os
import re
from typing import Any
import openai

LEGAL_DISCLAIMER = (
    "DISCLAIMER: This analysis provides general educational legal information regarding Pakistani law "
    "and does not constitute formal legal advice or an attorney-client relationship. "
    "Statutory provisions are subject to judicial interpretation and legislative amendment. "
    "For actionable legal counsel on specific matters, consult an advocate registered with a Provincial Bar Council."
)


def _clean_secret_free_text(text: str) -> str:
    """Ensure no API keys leak in text output."""
    for key in ["LLM_API_KEY", "SEARCH_API_KEY"]:
        val = os.getenv(key)
        if val and len(val) > 4 and val in text:
            text = text.replace(val, "[REDACTED]")
    return text


def _extract_sources(legal_context: str) -> list[str]:
    """Extract source titles or URLs mentioned in context."""
    sources = []
    url_pattern = r"https?://[^\s<>\"']+"
    urls = re.findall(url_pattern, legal_context)
    for u in urls:
        if u not in sources:
            sources.append(u)

    acts = [
        "Prevention of Electronic Crimes Act, 2016 (PECA)",
        "Pakistan Penal Code (Act XLV of 1860)",
        "Constitution of the Islamic Republic of Pakistan, 1973",
        "Protection Against Harassment of Women at the Workplace Act, 2010",
        "Code of Criminal Procedure, 1898 (CrPC)",
        "Family Courts Act, 1964",
    ]
    for act in acts:
        if any(term in legal_context.lower() for term in act.lower().split()[:2]):
            if act not in sources:
                sources.append(act)

    return sources


def _deterministic_explanation(question: str, legal_context: str, language: str = "English") -> dict[str, Any]:
    """Generate a clean, deterministic legal explanation grounded strictly in the provided context."""
    sources = _extract_sources(legal_context)

    penalties = []
    penalty_matches = re.findall(
        r"(punished with [^\.\;\n]+|imprisonment [^\.\;\n]+|fine [^\.\;\n]+)",
        legal_context,
        re.IGNORECASE,
    )
    for p in penalty_matches[:3]:
        p_clean = p.strip()
        if p_clean not in penalties:
            penalties.append(p_clean)

    section_matches = re.findall(r"(?:Section|Article)\s*[0-9]+[a-zA-Z]?[^\n\:\.]*", legal_context, re.IGNORECASE)
    referenced_sections = list(dict.fromkeys([s.strip() for s in section_matches[:4]]))

    summary_lines = []
    summary_lines.append(f"In response to your query regarding '{question}', the retrieved legal context establishes the following:")

    if referenced_sections:
        summary_lines.append(f"• Applicable statutory provisions identified: {', '.join(referenced_sections)}.")

    if penalties:
        summary_lines.append(f"• Prescribed statutory penalties noted in retrieved text: {'; '.join(penalties)}.")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", legal_context) if len(s.strip()) > 30]
    if sentences:
        summary_lines.append(f"• Core statutory principle: \"{sentences[0]}\"")
        if len(sentences) > 1 and len(summary_lines) < 4:
            summary_lines.append(f"• Supporting provision: \"{sentences[1]}\"")

    explanation_body = "\n\n".join(summary_lines)

    qualifications = [
        "Criminal offences require formal registration of an FIR or a complaint before the authorized agency (e.g. FIA Cyber Crime Wing for PECA, or local police station for PPC).",
        "The standard of proof in Pakistani criminal jurisprudence requires proving the offence beyond reasonable doubt with admissible evidence.",
        "Provincial variations or subsequent high court/supreme court precedents may interpret or qualify these statutory provisions.",
    ]

    uncertainty = (
        "This explanation is derived strictly from the supplied textual context. If specific amendments or "
        "rules have been notified after the cited date, or if specific jurisdiction issues apply (e.g. ICT vs Provinces), "
        "further verification against the latest gazette is recommended."
    )

    return {
        "question": question,
        "language": language,
        "plain_language_explanation": explanation_body,
        "important_qualifications": qualifications,
        "source_references": sources if sources else ["Official Pakistan Code (https://pakistancode.gov.pk)"],
        "uncertainty_notes": uncertainty,
        "disclaimer": LEGAL_DISCLAIMER,
        "generator": "deterministic_context_synthesizer",
    }


def legal_explanation(question: str, legal_context: str, language: str = "English") -> dict[str, Any]:
    """Transform retrieved legal context into an understandable explanation.

    Args:
        question: The user's original question.
        legal_context: The retrieved passages and source references.
        language: Response language, defaulting to English.

    Returns:
        Structured explanation with qualifications, sources, uncertainty, and disclaimers.
    """
    if not isinstance(question, str) or not question.strip():
        return {
            "plain_language_explanation": "Invalid input: question must be provided.",
            "important_qualifications": [],
            "source_references": [],
            "uncertainty_notes": "No question provided.",
            "disclaimer": LEGAL_DISCLAIMER,
            "status": "error",
        }

    clean_question = question.strip()
    clean_context = legal_context.strip() if isinstance(legal_context, str) else ""

    if not clean_context or len(clean_context) < 15 or "No matching legal passages" in clean_context:
        return {
            "question": clean_question,
            "language": language,
            "plain_language_explanation": (
                "Insufficient legal context was provided to establish the legal position under Pakistani law. "
                "No verified statutory provisions or authoritative excerpts were supplied. "
                "To answer your question reliably, please retrieve the relevant statutory provisions or official documents first."
            ),
            "important_qualifications": [
                "Cannot draw legal conclusions without verified statutory text.",
                "Consult official sources such as Pakistan Code (https://pakistancode.gov.pk).",
            ],
            "source_references": ["Official Pakistan Code: https://pakistancode.gov.pk"],
            "uncertainty_notes": "High uncertainty: Lack of verified legal evidence prevents substantive explanation.",
            "disclaimer": LEGAL_DISCLAIMER,
            "status": "insufficient_context",
        }

    api_key = os.getenv("LLM_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if provider in ["gemini", "google"] or (gemini_key and not api_key):
        provider = "gemini"
        api_key = gemini_key or api_key
        base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        if model in ["gpt-4o-mini", ""]:
            model = "gemini-1.5-flash"

    if api_key and provider not in ["demo", "none", ""]:
        try:
            client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=15.0)
            system_prompt = (
                "You are an expert legal assistant specializing in Pakistani law. "
                "Your role is to explain legal information clearly and accurately. "
                "CRITICAL RULES:\n"
                "1. Base all legal claims ONLY on the supplied legal context.\n"
                "2. DO NOT invent legislation, penalties, or procedures not present in the context.\n"
                "3. If the context is insufficient to answer any part of the question, explicitly state so.\n"
                "4. Return your output as a valid JSON object matching the required schema:\n"
                "{\n"
                '  "plain_language_explanation": "clear paragraph explanation",\n'
                '  "important_qualifications": ["qualification 1", "qualification 2"],\n'
                '  "source_references": ["source 1", "source 2"],\n'
                '  "uncertainty_notes": "notes on limitations or unresolved questions"\n'
                "}"
            )

            user_prompt = f"User Question: {clean_question}\nLanguage: {language}\n\nSupplied Legal Context:\n{clean_context}"

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_text)

            return {
                "question": clean_question,
                "language": language,
                "plain_language_explanation": parsed.get("plain_language_explanation", ""),
                "important_qualifications": parsed.get("important_qualifications", []),
                "source_references": parsed.get("source_references", _extract_sources(clean_context)),
                "uncertainty_notes": parsed.get("uncertainty_notes", "Interpretation based strictly on supplied provisions."),
                "disclaimer": LEGAL_DISCLAIMER,
                "generator": f"llm_{provider}_{model}",
                "status": "success",
            }
        except Exception:
            pass

    result = _deterministic_explanation(clean_question, clean_context, language)
    result["status"] = "success"
    return result
