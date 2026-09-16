"""
Structure Agent
-----------------
Analyzes a single Python file for code quality / maintainability issues using
Python's built-in `ast` module — no external tool needed, which keeps this
agent fast and dependency-free.

Checks:
  - functions missing docstrings
  - functions that are too long (line count over threshold)
  - functions with too many parameters
  - classes missing docstrings
  - deeply nested control flow (rough complexity signal)

Usage:
    from agents.structure_agent import analyze_file
    report = analyze_file("path/to/file.py")
"""

import ast
import json
import os
from dataclasses import asdict

from agents.schema import Finding, AgentReport

MAX_FUNCTION_LINES = 40
MAX_PARAMS = 5
MAX_NESTING_DEPTH = 4


def _function_length(node: ast.FunctionDef) -> int:
    if not node.body:
        return 0
    return node.body[-1].end_lineno - node.lineno + 1


def _max_nesting_depth(node: ast.AST, depth: int = 0) -> int:
    nesting_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With)
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child, nesting_nodes) else depth
        max_depth = max(max_depth, _max_nesting_depth(child, child_depth))
    return max_depth


def _check_function(node: ast.FunctionDef) -> list[Finding]:
    findings = []

    if not ast.get_docstring(node):
        findings.append(
            Finding(
                line=node.lineno,
                severity="low",
                confidence="high",
                category="missing_docstring",
                description=f"Function '{node.name}' has no docstring.",
                source="structure",
            )
        )

    length = _function_length(node)
    if length > MAX_FUNCTION_LINES:
        findings.append(
            Finding(
                line=node.lineno,
                severity="medium",
                confidence="high",
                category="long_function",
                description=f"Function '{node.name}' is {length} lines long "
                             f"(threshold: {MAX_FUNCTION_LINES}). Consider splitting it up.",
                source="structure",
            )
        )

    num_params = len(node.args.args)
    if num_params > MAX_PARAMS:
        findings.append(
            Finding(
                line=node.lineno,
                severity="low",
                confidence="high",
                category="too_many_parameters",
                description=f"Function '{node.name}' has {num_params} parameters "
                             f"(threshold: {MAX_PARAMS}). Consider a config object or fewer args.",
                source="structure",
            )
        )

    depth = _max_nesting_depth(node)
    if depth > MAX_NESTING_DEPTH:
        findings.append(
            Finding(
                line=node.lineno,
                severity="medium",
                confidence="medium",
                category="deep_nesting",
                description=f"Function '{node.name}' has nesting depth {depth} "
                             f"(threshold: {MAX_NESTING_DEPTH}). Consider early returns or extraction.",
                source="structure",
            )
        )

    return findings


def _check_class(node: ast.ClassDef) -> list[Finding]:
    findings = []
    if not ast.get_docstring(node):
        findings.append(
            Finding(
                line=node.lineno,
                severity="low",
                confidence="high",
                category="missing_docstring",
                description=f"Class '{node.name}' has no docstring.",
                source="structure",
            )
        )
    return findings


def analyze_file(filepath: str, use_llm: bool = False) -> AgentReport:
    # use_llm accepted for interface parity with security_agent, unused for now
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)

    with open(filepath, "r") as f:
        code = f.read()

    findings: list[Finding] = []
    try:
        tree = ast.parse(code, filename=filepath)
    except SyntaxError as e:
        return AgentReport(
            agent="structure",
            file=filepath,
            findings=[],
            summary=f"Could not parse file: {e}",
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            findings.extend(_check_function(node))
        elif isinstance(node, ast.ClassDef):
            findings.extend(_check_class(node))

    summary = f"{len(findings)} structural/maintainability issue(s) found."

    return AgentReport(
        agent="structure",
        file=filepath,
        findings=[asdict(f) for f in findings],
        summary=summary,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python structure_agent.py <path_to_python_file>")
        sys.exit(1)

    report = analyze_file(sys.argv[1])
    print(json.dumps(report.to_dict(), indent=2))
