"""Tests for the four Pakistan Law MCP tools."""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from pakistan_law_ai.mcp.tools.web_search import web_search
from pakistan_law_ai.mcp.tools.law_lookup import law_lookup
from pakistan_law_ai.mcp.tools.document_search import document_search
from pakistan_law_ai.mcp.tools.legal_explanation import legal_explanation, LEGAL_DISCLAIMER


class TestWebSearchTool:
    """Test web_search tool functionality, validation, and demo mode."""

    def test_input_validation_empty_query(self):
        result = web_search("")
        assert result["status"] == "error"
        assert "non-empty string" in result["error_message"]

    def test_input_validation_excessive_length(self):
        result = web_search("A" * 600)
        assert result["status"] == "error"
        assert "exceeds maximum limit" in result["error_message"]

    def test_missing_credentials_useful_error(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("SEARCH_API_KEY", "")
        result = web_search("cyber crime law")
        assert result["status"] == "error"
        assert "Missing SEARCH_API_KEY" in result["error_message"]

    def test_demo_mode_returns_official_urls(self, monkeypatch):
        monkeypatch.setenv("SEARCH_PROVIDER", "demo")
        result = web_search("cyber harassment and stalking")
        assert result["status"] == "demo_mode"
        assert len(result["results"]) > 0
        first = result["results"][0]
        assert "title" in first
        assert "snippet" in first
        assert "url" in first
        assert "domain" in first
        assert "pakistancode.gov.pk" in first["url"]

    def test_secret_not_leaked_in_errors(self, monkeypatch):
        secret_key = "super_secret_api_key_12345"
        monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
        monkeypatch.setenv("SEARCH_API_KEY", secret_key)

        with patch("httpx.Client.post", side_effect=Exception(f"Connection failed for {secret_key}")):
            result = web_search("pakistan constitutional rights")
            assert result["status"] == "error"
            assert secret_key not in result["error_message"]
            assert "[REDACTED]" in result["error_message"]


class TestLawLookupTool:
    """Test law_lookup tool for statutory provisions and verified sections."""

    def test_input_validation_empty_query(self):
        res = law_lookup("")
        assert res["verification_status"] == "unverified"
        assert "Query must be a non-empty string" in res["error_message"]

    def test_input_validation_length(self):
        res = law_lookup("X" * 600)
        assert res["verification_status"] == "unverified"
        assert "exceeds maximum limit" in res["error_message"]

    def test_verified_lookup_peca(self):
        res = law_lookup("Section 21 PECA cyber harassment")
        assert res["verification_status"] == "verified_statute"
        assert "Prevention of Electronic Crimes Act" in res["law_name"]
        assert "Section / Article 21" in res["section"]
        assert "pakistancode.gov.pk" in res["source_url"]
        assert len(res["retrieved_text"]) > 20

    def test_verified_lookup_ppc(self):
        res = law_lookup("Section 509 PPC insult to modesty of woman")
        assert res["verification_status"] == "verified_statute"
        assert "Pakistan Penal Code" in res["law_name"]
        assert "509" in res["section"]

    def test_unverified_provision_does_not_fabricate(self):
        res = law_lookup("Section 9999 Nonexistent Martian Code")
        assert res["verification_status"] == "unverified"
        assert "No verified Pakistani statutory provision" in res["retrieved_text"]


class TestDocumentSearchTool:
    """Test document_search tool across the statutory corpus."""

    def test_input_validation_empty_query(self):
        res = document_search("")
        assert res["status"] == "error"
        assert "Query must be a non-empty string" in res["error_message"]

    def test_search_finds_relevant_passages(self):
        res = document_search("bail non-bailable offence", max_results=3)
        assert res["status"] == "success"
        assert res["count"] > 0
        first = res["passages"][0]
        assert "document_title" in first
        assert "passage" in first
        assert "source_type" in first
        assert "source_url" in first

    def test_unmatched_search_honest_response(self):
        res = document_search("quantum teleportation interstellar space")
        assert res["status"] == "not_found"
        assert res["count"] == 0
        assert "No matching legal passages" in res["explanation"]


class TestLegalExplanationTool:
    """Test legal_explanation tool plain-language generation and grounding."""

    def test_input_validation_empty_question(self):
        res = legal_explanation("", "some legal context")
        assert res["status"] == "error"

    def test_insufficient_context_honest_flagging(self):
        res = legal_explanation("What are the penalties?", "")
        assert res["status"] == "insufficient_context"
        assert "Insufficient legal context" in res["plain_language_explanation"]
        assert "High uncertainty" in res["uncertainty_notes"]

    def test_deterministic_explanation_grounded(self):
        context = (
            "Section 21 of PECA 2016: Whoever intentionally displays information harming modesty "
            "shall be punished with imprisonment which may extend to five years or with fine. "
            "Official URL: https://pakistancode.gov.pk/peca"
        )
        res = legal_explanation("What is the penalty under Section 21 PECA?", context)
        assert res["status"] == "success"
        assert "five years" in res["plain_language_explanation"].lower() or "punished with" in res["plain_language_explanation"].lower()
        assert len(res["important_qualifications"]) > 0
        assert len(res["source_references"]) > 0
        assert LEGAL_DISCLAIMER in res["disclaimer"]
