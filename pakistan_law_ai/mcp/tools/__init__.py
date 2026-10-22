"""MCP tools for Pakistan Law AI Agent."""

from pakistan_law_ai.mcp.tools.web_search import web_search, search_web
from pakistan_law_ai.mcp.tools.law_lookup import law_lookup
from pakistan_law_ai.mcp.tools.document_search import document_search
from pakistan_law_ai.mcp.tools.legal_explanation import legal_explanation, LEGAL_DISCLAIMER

__all__ = [
    "web_search",
    "search_web",
    "law_lookup",
    "document_search",
    "legal_explanation",
    "LEGAL_DISCLAIMER",
]
