"""Custom Model Context Protocol (MCP) server for Pakistani Law."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configure logging to sys.stderr so MCP stdio JSON-RPC transport on stdout remains uncorrupted
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pakistan_law_mcp_server")

from mcp.server.mcpserver import MCPServer

from pakistan_law_ai.mcp.tools.web_search import search_web as _search_web
from pakistan_law_ai.mcp.tools.law_lookup import law_lookup as _law_lookup
from pakistan_law_ai.mcp.tools.document_search import document_search as _document_search
from pakistan_law_ai.mcp.tools.legal_explanation import legal_explanation as _legal_explanation

# Instantiate custom MCP server
server = MCPServer(
    name="pakistan-law-server",
    instructions="Authoritative Pakistani legal research server exposing web search, statutory lookup, document retrieval, and legal explanation tools.",
)


@server.tool(
    name="web_search",
    description=(
        "Search the web for information relevant to a question about Pakistani law. "
        "Returns titles, snippets, source URLs, and domains from authoritative Pakistani sources."
    ),
)
def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web for information relevant to Pakistani legal questions."""
    logger.info("Executing web_search with query=%r, max_results=%d", query, max_results)
    return _search_web(query=query, max_results=max_results)


@server.tool(
    name="law_lookup",
    description=(
        "Retrieve specific laws, acts, sections, legal provisions, or statutory references "
        "relevant to a question under Pakistani jurisdiction (e.g. PECA 2016, PPC 1860, Constitution 1973)."
    ),
)
def law_lookup(query: str, jurisdiction: str = "Pakistan") -> dict[str, Any]:
    """Retrieve specific Pakistani laws, acts, sections, or verified provisions."""
    logger.info("Executing law_lookup with query=%r, jurisdiction=%r", query, jurisdiction)
    return _law_lookup(query=query, jurisdiction=jurisdiction)


@server.tool(
    name="document_search",
    description=(
        "Search authoritative Pakistani legal documents and statutes, retrieving relevant passages, "
        "sections, source types, and URLs."
    ),
)
def document_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search legal documents and retrieve relevant statutory passages."""
    logger.info("Executing document_search with query=%r, max_results=%d", query, max_results)
    return _document_search(query=query, max_results=max_results)


@server.tool(
    name="legal_explanation",
    description=(
        "Transform retrieved legal provisions and context into a plain-language explanation with "
        "qualifications, source citations, uncertainty notes, and legal disclaimers."
    ),
)
def legal_explanation(question: str, legal_context: str, language: str = "English") -> dict[str, Any]:
    """Transform retrieved legal context into an understandable explanation."""
    logger.info("Executing legal_explanation for question=%r, language=%r", question, language)
    return _legal_explanation(question=question, legal_context=legal_context, language=language)


def main() -> None:
    """Run the MCP server over standard input/output transport."""
    logger.info("Starting Pakistan Law MCP Server on stdio transport...")
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
