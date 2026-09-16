"""
Security Agent
---------------
Analyzes a single Python file for security vulnerabilities.

Design principle: don't trust an LLM alone to find vulnerabilities (it hallucinates).
Instead, ground the analysis with Bandit (a real static analysis tool), then use
an LLM to explain, prioritize, and add context to what Bandit found — and to catch
a few categories Bandit doesn't cover well (e.g. logic-level issues).

Usage:
    from agents.security_agent import analyze_file
    report = analyze_file("path/to/file.py")
"""

import json
import subprocess
import os
from dataclasses import asdict

from agents.schema import Finding, AgentReport


def run_bandit(filepath: str) -> list[dict]:
    """Run Bandit static analysis on a single file and return raw results."""
    result = subprocess.run(
        ["bandit", "-f", "json", filepath],
        capture_output=True,
        text=True,
    )
    # Bandit exits with non-zero status when it finds issues — that's expected,
    # not a failure. Only treat it as an error if there's no parseable output.
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return data.get("results", [])


def _map_bandit_findings(raw_results: list[dict]) -> list[Finding]:
    findings = []
    for r in raw_results:
        findings.append(
            Finding(
                line=r.get("line_number", 0),
                severity=r.get("issue_severity", "unknown").lower(),
                confidence=r.get("issue_confidence", "unknown").lower(),
                category=r.get("test_name", "unknown"),
                description=r.get("issue_text", ""),
                source="bandit",
            )
        )
    return findings


def _enrich_with_llm(code: str, findings: list[Finding]) -> tuple[list[Finding], str]:
    """
    Optional enrichment step: send the code + Bandit findings to Claude to get a
    plain-English summary and catch anything Bandit's rule-based checks might miss.
    Falls back gracefully (no-op) if no API key is configured, so the agent still
    works end-to-end without it.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        summary = (
            f"{len(findings)} issue(s) found via static analysis. "
            "Set ANTHROPIC_API_KEY to enable LLM-based summary and enrichment."
        )
        return findings, summary

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        findings_text = "\n".join(
            f"- Line {f.line} [{f.severity}] {f.category}: {f.description}"
            for f in findings
        ) or "None found by static analysis."

        prompt = f"""You are a security code reviewer. A static analysis tool (Bandit)
found the following issues in this Python file:

{findings_text}

Here is the code:
```python
{code}
```

1. Write a 2-3 sentence plain-English summary of the overall security posture.
2. If you notice any additional logic-level security issues Bandit would not catch
   (e.g. broken auth logic, insecure design decisions), list them briefly.
Respond in under 150 words, no preamble."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return findings, summary
    except Exception as e:
        # Never let enrichment failures break the core pipeline
        return findings, f"LLM enrichment unavailable ({e}). Showing static analysis results only."


def analyze_file(filepath: str, use_llm: bool = True) -> AgentReport:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)

    with open(filepath, "r") as f:
        code = f.read()

    raw_bandit = run_bandit(filepath)
    findings = _map_bandit_findings(raw_bandit)

    if use_llm:
        findings, summary = _enrich_with_llm(code, findings)
    else:
        summary = f"{len(findings)} issue(s) found via static analysis."

    return AgentReport(
        agent="security",
        file=filepath,
        findings=[asdict(f) for f in findings],
        summary=summary,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python security_agent.py <path_to_python_file>")
        sys.exit(1)

    report = analyze_file(sys.argv[1])
    print(json.dumps(report.to_dict(), indent=2))
