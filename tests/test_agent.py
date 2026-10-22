"""Tests for the Pakistan Law AI Agent."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
import pytest

from pakistan_law_ai.agents.law_agent import PakistanLawAgent, LEGAL_DISCLAIMER
import main


class TestPakistanLawAgent:
    """Automated tests for agent behavior, tool execution, and guardrails."""

    @pytest.mark.asyncio
    async def test_agent_answers_cyber_harassment_query(self):
        """Test agent answering cyber harassment question using MCP tools."""
        agent = PakistanLawAgent()
        result = await agent.answer("What are the legal consequences of cyber harassment in Pakistan?")

        assert "answer" in result
        assert len(result["answer"]) > 50
        assert "tools_used" in result
        assert len(result["tools_used"]) > 0
        assert "law_lookup" in result["tools_used"]
        assert len(result["sources"]) > 0
        assert LEGAL_DISCLAIMER in result["disclaimer"]

    @pytest.mark.asyncio
    async def test_agent_handles_unrelated_query_gracefully(self):
        """Test that agent identifies off-scope questions without running irrelevant legal tools."""
        agent = PakistanLawAgent()
        result = await agent.answer("How do I make chocolate chip cookies at home?")

        assert "outside Pakistani legal topics" in result["answer"]
        assert len(result["tools_used"]) == 0

    @pytest.mark.asyncio
    async def test_agent_handles_empty_search_honestly(self):
        """Test that missing legal evidence produces an honest response rather than fabrication."""
        agent = PakistanLawAgent()
        result = await agent.answer("What does Section 9999 of the Interplanetary Cyber Treaty state?")

        assert "Unverified" in result["answer"] or "Insufficient" in result["answer"] or "not found" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_agent_maintains_conversation_history(self):
        """Test conversational memory persists context across consecutive questions."""
        agent = PakistanLawAgent()
        await agent.answer("Tell me about Section 21 of PECA.")
        initial_history_len = len(agent.history)
        assert initial_history_len >= 3  # System prompt + user + assistant

        await agent.answer("What penalties does it prescribe?")
        assert len(agent.history) > initial_history_len

        agent.clear_history()
        assert len(agent.history) == 1

    @pytest.mark.asyncio
    async def test_agent_iteration_limit(self, monkeypatch):
        """Verify the agent stops when tool iteration limit is reached."""
        monkeypatch.setenv("MAX_TOOL_ITERATIONS", "1")
        monkeypatch.setenv("LLM_API_KEY", "mock_key")
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "web_search"
        mock_tool_call.function.arguments = '{"query": "Pakistan law"}'

        mock_msg = MagicMock()
        mock_msg.tool_calls = [mock_tool_call]
        mock_msg.content = None

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=mock_msg)]

        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_resp
            mock_openai_cls.return_value = mock_client

            agent = PakistanLawAgent(max_iterations=1)
            res = await agent.answer("What is the law?")
            assert "reached the maximum iteration limit" in res["answer"].lower()

    @pytest.mark.asyncio
    async def test_agent_mocked_llm_tool_sequence(self, monkeypatch):
        """Test agent executing a sequence of mocked LLM tool calls."""
        monkeypatch.setenv("LLM_API_KEY", "mock_key")
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        # Step 1: LLM requests law_lookup
        call1 = MagicMock()
        call1.id = "call_1"
        call1.function.name = "law_lookup"
        call1.function.arguments = '{"query": "PECA Section 21"}'

        msg1 = MagicMock()
        msg1.tool_calls = [call1]
        msg1.content = None
        resp1 = MagicMock(choices=[MagicMock(message=msg1)])

        # Step 2: LLM provides final answer based on tool output
        msg2 = MagicMock()
        msg2.tool_calls = None
        msg2.content = "Under Section 21 of PECA 2016, cyber harassment is punishable with up to 5 years imprisonment. See https://pakistancode.gov.pk"
        resp2 = MagicMock(choices=[MagicMock(message=msg2)])

        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = [resp1, resp2]
            mock_openai_cls.return_value = mock_client

            agent = PakistanLawAgent()
            res = await agent.answer("What is PECA section 21?")
            assert "law_lookup" in res["tools_used"]
            assert "5 years" in res["answer"]
            assert any("pakistancode.gov.pk" in s["url"] for s in res["sources"])

    @pytest.mark.asyncio
    async def test_terminal_chat_graceful_exit(self, monkeypatch):
        """Test that the terminal interface exits gracefully on 'exit'."""
        inputs = iter(["exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        # chat_loop should finish without unhandled exceptions
        await main.chat_loop()
