"""
CLI entry point for IntellectFlow.

Run:
    python main.py samples/vulnerable_example.py
    python main.py samples/vulnerable_example.py --format markdown

Runs the Security Agent and Structure Agent in parallel via the LangGraph
orchestrator, then prints a single synthesized report (JSON or Markdown).
"""

import argparse
import json
import sys

from orchestrator.graph import run_audit
from reports.markdown import render_markdown


def main():
    parser = argparse.ArgumentParser(description="Run an IntellectFlow code audit.")
    parser.add_argument("filepath", help="Path to a Python file to audit")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args()

    report = run_audit(args.filepath)

    if args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
