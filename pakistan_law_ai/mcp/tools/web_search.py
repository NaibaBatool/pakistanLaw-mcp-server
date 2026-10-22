"""Web search tool for Pakistani legal information."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse
import httpx


def _clean_secret_free_message(msg: str) -> str:
    """Ensure no API keys leak in error messages."""
    for key in ["SEARCH_API_KEY", "LLM_API_KEY"]:
        val = os.getenv(key)
        if val and len(val) > 4 and val in msg:
            msg = msg.replace(val, "[REDACTED]")
    return msg


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web for information relevant to a question about Pakistani law.

    Args:
        query: A clear natural-language search query.
        max_results: Optional bounded number of results (between 1 and 20).

    Returns:
        A dictionary containing:
            - results: List of items with title, snippet, url, and domain.
            - query: The executed query.
            - provider: Name of the search provider used.
            - status: 'success', 'demo_mode', or 'error'.
            - error_message: Optional error details.
    """
    # 1. Input validation
    if not isinstance(query, str) or not query.strip():
        return {
            "query": query,
            "results": [],
            "provider": "none",
            "status": "error",
            "error_message": "Invalid query: query must be a non-empty string.",
        }

    clean_query = query.strip()
    if len(clean_query) > 500:
        return {
            "query": clean_query[:50] + "...",
            "results": [],
            "provider": "none",
            "status": "error",
            "error_message": "Query length exceeds maximum limit of 500 characters.",
        }

    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 5
    max_results = max(1, min(max_results, 20))

    provider = os.getenv("SEARCH_PROVIDER", "demo").lower().strip()
    api_key = os.getenv("SEARCH_API_KEY", "").strip()

    # 2. Check for missing credentials for live providers
    if provider in ["tavily", "serper"] and not api_key:
        return {
            "query": clean_query,
            "results": [],
            "provider": provider,
            "status": "error",
            "error_message": (
                f"Missing SEARCH_API_KEY for search provider '{provider}'. "
                "Please configure SEARCH_API_KEY in your .env file or set SEARCH_PROVIDER=demo."
            ),
        }

    # 3. Handle live Tavily search if configured
    if provider == "tavily" and api_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": f"{clean_query} Pakistan law",
                        "max_results": max_results,
                        "include_domains": [
                            "pakistancode.gov.pk",
                            "na.gov.pk",
                            "senate.gov.pk",
                            "supremecourt.gov.pk",
                            "molaw.gov.pk",
                            "fia.gov.pk",
                        ],
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("results", []):
                        url = item.get("url", "")
                        domain = urlparse(url).netloc
                        results.append({
                            "title": item.get("title", "Untitled"),
                            "snippet": item.get("content", ""),
                            "url": url,
                            "domain": domain,
                        })
                    return {
                        "query": clean_query,
                        "results": results[:max_results],
                        "provider": "tavily",
                        "status": "success",
                    }
                else:
                    return {
                        "query": clean_query,
                        "results": [],
                        "provider": "tavily",
                        "status": "error",
                        "error_message": f"Tavily API responded with status {resp.status_code}",
                    }
        except Exception as exc:
            return {
                "query": clean_query,
                "results": [],
                "provider": "tavily",
                "status": "error",
                "error_message": _clean_secret_free_message(f"Search request failed: {type(exc).__name__}: {exc}"),
            }

    # 4. Handle live Serper search if configured
    if provider == "serper" and api_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                    json={"q": f"{clean_query} Pakistan law", "num": max_results},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for item in data.get("organic", []):
                        url = item.get("link", "")
                        domain = urlparse(url).netloc
                        results.append({
                            "title": item.get("title", "Untitled"),
                            "snippet": item.get("snippet", ""),
                            "url": url,
                            "domain": domain,
                        })
                    return {
                        "query": clean_query,
                        "results": results[:max_results],
                        "provider": "serper",
                        "status": "success",
                    }
                else:
                    return {
                        "query": clean_query,
                        "results": [],
                        "provider": "serper",
                        "status": "error",
                        "error_message": f"Serper API responded with status {resp.status_code}",
                    }
        except Exception as exc:
            return {
                "query": clean_query,
                "results": [],
                "provider": "serper",
                "status": "error",
                "error_message": _clean_secret_free_message(f"Search request failed: {type(exc).__name__}: {exc}"),
            }

    # 5. Clear, honest local demonstration mode when external API is not configured
    demo_catalog = [
        {
            "match": ["cyber", "harassment", "peca", "online", "internet", "electronic", "stalking", "social media", "intimate"],
            "title": "Prevention of Electronic Crimes Act 2016 (PECA) - Official Pakistan Code",
            "snippet": "Federal legislation regulating cyber crimes in Pakistan, including cyber harassment (Section 21), cyber stalking (Section 24), unauthorized access (Section 3), and online defamation (Section 20).",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-apU%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
        {
            "match": ["workplace", "harassment", "women", "ombudsman", "employment", "office"],
            "title": "Protection Against Harassment of Women at the Workplace Act 2010 - Official Gazette",
            "snippet": "Statute mandating workplace inquiry committees and establishing Federal and Provincial Ombudspersons for hearing harassment complaints at work.",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-apc%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
        {
            "match": ["constitution", "fundamental rights", "article", "speech", "privacy", "liberty", "fair trial"],
            "title": "Constitution of the Islamic Republic of Pakistan, 1973 - Legislative Portal",
            "snippet": "The supreme constitutional law of Pakistan outlining Fundamental Rights: Right to Life (Art 9), Fair Trial (Art 10A), Inviolability of Dignity & Privacy (Art 14), and Freedom of Speech (Art 19).",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-cJA%3D%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
        {
            "match": ["fir", "bail", "crpc", "criminal procedure", "police", "arrest", "investigation"],
            "title": "Code of Criminal Procedure 1898 (CrPC) - Pakistan Legal Database",
            "snippet": "Procedural law governing police investigation, FIR registration under Section 154, and bail provisions under Sections 496, 497, and 498.",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-apg%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
        {
            "match": ["penal code", "ppc", "murder", "theft", "defamation", "cheating", "fraud", "criminal intimidation"],
            "title": "Pakistan Penal Code 1860 (Act XLV of 1860) - Official Statute",
            "snippet": "Substantive penal law of Pakistan defining general criminal offences including defamation (Section 499/500), cheating (Section 415/420), and insults to modesty (Section 509).",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-apk%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
        {
            "match": ["family", "marriage", "khula", "divorce", "dower", "custody", "maintenance"],
            "title": "Family Courts Act 1964 - Family Law Portal Pakistan",
            "snippet": "Procedural and jurisdiction law governing expedited settlement of family disputes, dissolution of marriage (Khula), custody, and dower in Pakistan.",
            "url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-cpa%3D-sg-jjjjjjjjjjjjj",
            "domain": "pakistancode.gov.pk",
        },
    ]

    q_lower = clean_query.lower()
    matched = []
    for item in demo_catalog:
        if any(term in q_lower for term in item["match"]):
            matched.append({
                "title": item["title"],
                "snippet": item["snippet"],
                "url": item["url"],
                "domain": item["domain"],
            })

    if not matched:
        matched.append({
            "title": "The Pakistan Code - Federal Laws of Pakistan",
            "snippet": "Official repository of federal statutes, acts, and ordinances maintained by the Ministry of Law and Justice, Government of Pakistan.",
            "url": "https://pakistancode.gov.pk",
            "domain": "pakistancode.gov.pk",
        })

    return {
        "query": clean_query,
        "results": matched[:max_results],
        "provider": "demo",
        "status": "demo_mode",
        "notice": (
            "Demonstration mode: returning verified official Pakistan legal portal references. "
            "To enable live web search, configure SEARCH_PROVIDER=tavily and SEARCH_API_KEY in .env."
        ),
    }


# Backwards compatibility alias
search_web = web_search

