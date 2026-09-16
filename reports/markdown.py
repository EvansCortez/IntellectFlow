"""Convert a synthesized audit report dict into readable Markdown."""

SEVERITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢", "unknown": "⚪"}


def render_markdown(report: dict) -> str:
    totals = report.get("totals", {})
    findings = report.get("findings", [])
    summaries = report.get("agent_summaries", {})
    filepath = report.get("file", "unknown")

    lines = [
        f"# IntellectFlow Audit Report",
        "",
        f"**File:** `{filepath}`",
        "",
        "## Summary",
        "",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| High     | {totals.get('high', 0)} |",
        f"| Medium   | {totals.get('medium', 0)} |",
        f"| Low      | {totals.get('low', 0)} |",
        f"| **Total** | **{totals.get('total', 0)}** |",
        "",
    ]

    if summaries:
        lines += ["## Agent Summaries", ""]
        for agent, summary in summaries.items():
            lines += [f"### {agent.title()}", "", summary, ""]

    if findings:
        lines += ["## Findings", ""]
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "unknown")
            emoji = SEVERITY_EMOJI.get(sev, "⚪")
            lines += [
                f"### {i}. {emoji} {sev.upper()} — {f.get('category', 'unknown')}",
                "",
                f"- **Line:** {f.get('line', '?')}",
                f"- **Confidence:** {f.get('confidence', 'unknown')}",
                f"- **Source:** {f.get('source', 'unknown')}",
                f"- **Description:** {f.get('description', '')}",
                "",
            ]
    else:
        lines += ["## Findings", "", "No issues found.", ""]

    return "\n".join(lines)
