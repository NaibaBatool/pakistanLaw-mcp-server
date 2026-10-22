# Pakistan Law AI Agent — MCP Server Implementation

An educational, beginner-friendly AI agent that helps users research and understand Pakistani law through a conversational terminal interface. The project demonstrates how an AI agent uses a custom **Model Context Protocol (MCP)** server to dynamically discover, select, and invoke relevant tools based on natural-language legal questions.

---

## 1. Architecture Overview

```
                      +-----------------------------+
                      |   Terminal Chat Interface   |
                      |          (main.py)          |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    PakistanLawAgent         |
                      |   (agents/law_agent.py)     |
                      +--------------+--------------+
                                     |
       MCP Client Connection (stdio) | Subprocess Discovery & Invocation
                                     v
                      +-----------------------------+
                      |   Pakistan Law MCP Server   |
                      |       (mcp/server.py)       |
                      +--------------+--------------+
                                     |
      +-----------------+------------+----+-------------------+
      |                 |                 |                   |
      v                 v                 v                   v
+------------+   +-------------+   +---------------+   +-------------------+
| web_search |   | law_lookup  |   |document_search|   | legal_explanation |
+------------+   +-------------+   +---------------+   +-------------------+
  (External /     (Verified Law     (Corpus Search      (Plain-Language
   Pak Code        Sections from     across Statutes     Synthesis with
   Portals)        Pakistan Code)    & Judgments)        Disclaimers)
```

### End-to-End Workflow Example
When a user asks:
> *"What are the legal consequences of cyber harassment in Pakistan?"*

1. **Analysis**: The agent receives the prompt and identifies "cyber harassment" under Pakistani federal jurisdiction.
2. **Tool Discovery**: The agent queries the MCP server over standard I/O (`stdio_client`) to discover registered tools and their schemas.
3. **Execution**:
   - Calls `law_lookup` to fetch verified statutory provisions (e.g. PECA 2016 Section 21 & Section 24).
   - Calls `document_search` to retrieve relevant excerpts and penalty clauses.
   - Calls `legal_explanation` to translate statutory provisions into plain English while attaching qualifications and disclaimers.
4. **Presentation**: The agent returns a structured answer citing exact statutory sections and official links (e.g., [The Pakistan Code](https://pakistancode.gov.pk)).

---

## 2. The Four MCP Tools

| Tool Name | Purpose | Default / Fallback Mode |
|---|---|---|
| `web_search` | Searches online legal resources with preference for official `.gov.pk` domains. | Supports Tavily and Serper APIs. If unconfigured, falls back to an offline demonstration mode returning verified government portals. |
| `law_lookup` | Retrieves verified statutory sections (e.g., PECA 2016, PPC 1860, Constitution 1973, CrPC 1898). | Queries verified legal documents in `data/documents/`. Never fabricates non-existent section numbers. |
| `document_search` | Keyword and token-based search across legal documents, statutes, and notices. | Scans structured JSON/Markdown legal corpora. Explains limitations if no matching provisions are found. |
| `legal_explanation` | Translates legal text into plain language, highlighting penalties, qualifications, and uncertainties. | Can use an LLM provider when configured; otherwise runs a deterministic synthesis template. |

---

## 3. Project Structure

```
law-mcp/
├── data/
│   └── documents/                  # Verified statutory provisions & acts
│       ├── peca_2016.json          # Prevention of Electronic Crimes Act 2016
│       ├── ppc_1860.json           # Pakistan Penal Code 1860
│       ├── constitution_1973.json  # Constitution of Pakistan 1973
│       ├── crpc_1898.json          # Code of Criminal Procedure 1898
│       ├── harassment_workplace_2010.json # Workplace Harassment Act 2010
│       ├── family_courts_1964.json # Family Courts Act 1964
│       └── README.md               # Guide to adding new legal statutes
├── pakistan_law_ai/
│   ├── __init__.py
│   ├── mcp/                        # Custom MCP Server Implementation
│   │   ├── __init__.py
│   │   ├── server.py               # FastMCP / MCPServer (stdio transport)
│   │   └── tools/                  # The 4 MCP tools
│   │       ├── __init__.py
│   │       ├── web_search.py
│   │       ├── law_lookup.py
│   │       ├── document_search.py
│   │       └── legal_explanation.py
│   └── agents/                     # Agent Implementation
│       ├── __init__.py
│       └── law_agent.py            # PakistanLawAgent with dynamic tool calling
├── agents/                         # Import proxy for agents.law_agent
│   ├── __init__.py
│   └── law_agent.py
├── tests/                          # 26 automated unit & integration tests
│   ├── test_tools.py               # Tests for all 4 MCP tools
│   ├── test_mcp_server.py          # Tests for MCP server & stdio client
│   └── test_agent.py               # Tests for agent reasoning, fallback & loops
├── .env.example                    # Template configuration
├── .gitignore
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Python dependencies
├── main.py                         # Interactive terminal chat entrypoint
└── README.md                       # Comprehensive documentation
```

---

## 4. Getting Started

### Step 1: Prerequisites
- Python 3.11 or newer (Python 3.11, 3.12, 3.13, 3.14, 3.15).
- Git installed on your machine.

### Step 2: Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to create your `.env` file:

```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Open `.env` and review the settings:
```ini
# LLM Configuration (Optional: runs in demo mode out-of-the-box if left blank)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_openai_or_groq_api_key_here

# Search Configuration (Optional: uses demo mode if left blank)
SEARCH_PROVIDER=demo
SEARCH_API_KEY=

# MCP Settings
MCP_TRANSPORT=stdio
MAX_TOOL_ITERATIONS=5
```

> **Note**: The application is fully functional **without paid API keys**. When `LLM_API_KEY` is omitted, the agent automatically utilizes a local deterministic reasoning orchestrator that connects to the real MCP server, invokes the MCP tools, and synthesizes source-grounded answers.

---

## 5. Running the Application

### Launch the Terminal Chat Interface
```bash
python main.py
```

### Example Questions to Try:
1. *"What are the legal consequences of cyber harassment in Pakistan?"*
2. *"What are the provisions for pre-arrest and post-arrest bail under the CrPC?"*
3. *"How does Pakistani law define workplace harassment under the 2010 Act?"*
4. *"What fundamental rights are protected under Article 9, 10A, and 14 of the Constitution?"*
5. *"What does Section 420 of the Pakistan Penal Code cover?"*

### Special Commands in Chat:
- `clear` or `reset`: Clears session conversation history.
- `exit` or `quit`: Exits the interactive chat gracefully.

---

## 6. Running the MCP Server Standalone
You can run the MCP server as a standalone subprocess listening on standard input/output:
```bash
python -m pakistan_law_ai.mcp.server
```
*(Diagnostic logs are piped exclusively to `stderr` to ensure the JSON-RPC communication on `stdout` is not corrupted).*

---

## 7. Running Automated Tests

Run the full automated test suite with pytest:
```bash
pytest -v
```

All 26 tests run offline without requiring paid API tokens:
- **`tests/test_tools.py`**: Validates input bounding, output structures, missing credentials handling, and API key redaction for all four tools.
- **`tests/test_mcp_server.py`**: Verifies tool registration and performs end-to-end MCP client-server integration testing over `stdio`.
- **`tests/test_agent.py`**: Tests LLM tool calling loops, mocked tool sequences, iteration bounding, conversation memory, and honest fallback on unverified provisions.

---

## 8. Security & Legal Safeguards

1. **No Hallucinated Provisions**: If a section number or statute cannot be verified in official records, the agent explicitly states that the provision is unverified.
2. **Secret Redaction**: API keys and environment variables are scrubbed from all error messages, logs, and tool results.
3. **Prompt Injection Resistance**: Retrieved web content and documents are treated as untrusted data and cannot override system-level safety directives.
4. **Input Length Limits**: User queries and parameters are clamped to prevent denial-of-service and buffer exhaustion.
5. **Bounded Tool Execution**: `MAX_TOOL_ITERATIONS` prevents runaway tool-calling loops.
6. **Statutory Disclaimers**: All responses clearly clarify that the platform provides educational legal information, not personalized legal advice or representation.

---

## 9. Official Pakistani Legal References
- **The Pakistan Code**: [https://pakistancode.gov.pk](https://pakistancode.gov.pk)
- **Supreme Court of Pakistan**: [https://supremecourt.gov.pk](https://supremecourt.gov.pk)
- **National Assembly of Pakistan**: [https://na.gov.pk](https://na.gov.pk)
- **Senate of Pakistan**: [https://senate.gov.pk](https://senate.gov.pk)
- **FIA Cyber Crime Wing**: [https://fia.gov.pk](https://fia.gov.pk)
