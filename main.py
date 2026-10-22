"""Terminal conversational interface for the Pakistan Law AI Agent."""

from __future__ import annotations

import asyncio
import sys
from pakistan_law_ai.agents.law_agent import PakistanLawAgent

BANNER = """
================================================================================
                    PAKISTAN LAW AI AGENT (MCP Powered)
================================================================================
Ask questions about Pakistani law and explore relevant legal sources.
Connects dynamically to the Pakistan Law MCP Server using stdio transport.

Commands:
  - Type your legal question in plain English or Urdu terms.
  - Type 'clear' to reset conversation history.
  - Type 'exit' or 'quit' to close the application.
================================================================================
"""

LEGAL_NOTICE = """
[!] NOTICE: This tool provides educational legal information and statutory provisions.
    It does not provide licensed legal advice or attorney representation.
"""


def format_status(msg: str) -> None:
    """Print an active progress indicator."""
    sys.stdout.write(f"\r\033[K[*] {msg}")
    sys.stdout.flush()


def clear_status() -> None:
    """Clear active progress line."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


async def chat_loop() -> None:
    """Main interactive chat loop."""
    print(BANNER)
    print(LEGAL_NOTICE)

    agent = PakistanLawAgent()

    while True:
        try:
            print("-" * 80)
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nExiting Pakistan Law AI Agent. Khuda Hafiz!\n")
                break

            if user_input.lower() in ["clear", "reset"]:
                agent.clear_history()
                print("\n[+] Conversation history reset successfully.")
                continue

            # Execute agent query with live status callback
            result = await agent.answer(user_input, status_callback=format_status)

            clear_status()
            print("\nPakistan Law AI Agent:")
            print(result.get("answer", ""))

            # Display tools used if any
            tools_used = result.get("tools_used", [])
            if tools_used:
                print(f"\n[MCP Tools Executed: {', '.join(tools_used)}]")

            # Display sources separately
            sources = result.get("sources", [])
            if sources:
                print("\nRelevant Legal Sources & Authorities:")
                for i, s in enumerate(sources, start=1):
                    title = s.get("title", "Official Source")
                    url = s.get("url", "")
                    print(f"  [{i}] {title}")
                    if url:
                        print(f"      URL: {url}")

            # Display disclaimer
            disclaimer = result.get("disclaimer")
            if disclaimer:
                print(f"\n{disclaimer}")

        except (KeyboardInterrupt, EOFError):
            print("\n\nSession terminated by user. Exiting...")
            break
        except Exception as err:
            clear_status()
            print(f"\n[Error]: An unexpected error occurred: {err}")


def main() -> None:
    """Application entrypoint."""
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
