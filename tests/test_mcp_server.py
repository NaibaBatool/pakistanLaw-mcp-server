"""Tests for the Pakistan Law MCP Server."""

from __future__ import annotations

import asyncio
import json
import sys
import pytest

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

from pakistan_law_ai.mcp.server import server


class TestMCPServerRegistration:
    """Test server instance configuration and registered tools."""

    def test_server_metadata(self):
        assert server.name == "pakistan-law-server"
        assert "Pakistani legal research" in server.instructions

    @pytest.mark.asyncio
    async def test_tools_registered_on_server(self):
        """Verify that all four required tools are registered."""
        tool_list = await server.list_tools()
        registered_names = [t.name for t in tool_list]

        assert "web_search" in registered_names
        assert "law_lookup" in registered_names
        assert "document_search" in registered_names
        assert "legal_explanation" in registered_names
        assert len(registered_names) == 4


class TestMCPStdioIntegration:
    """Integration test verifying real MCP Client-Server communication over stdio."""

    @pytest.mark.asyncio
    async def test_stdio_client_discovery_and_call(self):
        """Spin up server subprocess via stdio, discover tools, and execute a tool call."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "pakistan_law_ai.mcp.server"],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                init_result = await session.initialize()
                assert session.protocol_version is not None

                # Test tool discovery
                tools_result = await session.list_tools()
                discovered_names = {t.name for t in tools_result.tools}
                expected_names = {"web_search", "law_lookup", "document_search", "legal_explanation"}
                assert expected_names.issubset(discovered_names)

                # Test executing tool call over MCP protocol
                res = await session.call_tool("law_lookup", {"query": "cyber stalking PECA section 24"})
                assert res.content is not None
                assert len(res.content) > 0

                raw_text = res.content[0].text
                parsed = json.loads(raw_text)
                assert parsed.get("verification_status") == "verified_statute"
                assert "Prevention of Electronic Crimes Act" in parsed.get("law_name")
                assert "pakistancode.gov.pk" in parsed.get("source_url")
