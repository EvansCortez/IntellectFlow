# IntellectFlow
 
**A multi-agent AI system that automatically reviews code for bugs, security vulnerabilities, and quality issues — like an on-demand engineering team for your pull requests.**
 
Instead of a single LLM prompt guessing at "is this code good?", IntellectFlow coordinates multiple specialized agents — each focused on a narrow task — and synthesizes their findings into a single actionable report.
 
---
 
## How It Works
 
1. **Input**: A developer uploads a repository (or, eventually, triggers a webhook on push).
2. **Analysis**: The codebase is broken into manageable chunks and routed to specialized agents:
   - **Structure Agent** — analyzes code organization, complexity, and maintainability
   - **Security Agent** — checks for vulnerabilities (SQL injection, hardcoded secrets, unsafe deserialization, etc.), grounded with real static analysis tools rather than LLM judgment alone
   - **Optimization Agent** — flags performance bottlenecks and inefficient patterns
3. **Synthesis**: An orchestrator agent merges all findings, resolves overlaps, and produces a single structured report.
4. **Output**: A clean markdown/HTML audit report with severity-ranked findings.
---
 
## Tech Stack
 
| Layer | Tools |
|---|---|
| Backend | Python (FastAPI) |
| AI Orchestration | LangGraph |
| Static Analysis Grounding | Bandit (security), AST parsing (structure) |
| Frontend | Next.js / TypeScript *(planned)* |
| Report Output | Markdown / JSON |
 
---
 
## Why This Project
 
Most "AI code review" demos are a single LLM call on a small snippet. IntellectFlow is built to handle **real, large, messy codebases** — which means solving problems most tutorials skip:
 
- Chunking and context management for repos too large for a single context window
- Structured agent-to-agent communication and hand-off (not just sequential prompting)
- Grounding LLM output with actual static analysis tools instead of trusting hallucination-prone "vibes-based" vulnerability detection
- Designing for eventual async/background processing (webhook-triggered runs)
---
 
## Quick Start

Requires **Python 3.11–3.13** (3.14 is not yet supported by all dependencies).

```bash
# Clone and enter the repo
cd IntellectFlow

# Create a virtual environment and install dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: enable LLM enrichment (Claude summary + logic-level checks)
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Run an audit on the sample vulnerable file
python main.py samples/vulnerable_example.py

# Or get a Markdown report
python main.py samples/vulnerable_example.py --format markdown

# Start the API server
uvicorn api.app:app --reload
# Then POST a .py file to http://127.0.0.1:8000/audit or /audit/markdown
```

The CLI runs the **Security Agent** and **Structure Agent** in parallel via LangGraph, then prints a single report (JSON or Markdown).

---

## Status

🚧 **Early development.**

- [x] Core single-agent pipeline (security agent, JSON output)
- [x] Multi-agent orchestration (LangGraph)
- [x] Static analysis grounding layer (Bandit + AST)
- [x] Markdown report generation
- [x] FastAPI endpoint
- [ ] Frontend dashboard
- [ ] GitHub webhook integration

---

## License

MIT
 

