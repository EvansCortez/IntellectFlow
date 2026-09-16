"""
Orchestrator
-------------
Coordinates multiple agents using LangGraph and synthesizes their findings into
a single report.

Graph shape (current):

    START -> security_node -\
                              -> synthesize_node -> END
    START -> structure_node -/

security_node and structure_node run independently (no dependency between them),
then synthesize_node merges both sets of findings into one report.

This is deliberately simple for now — a fan-out/fan-in graph. As more agents are
added (e.g. an optimization agent), they plug into the same pattern: add a node,
add an edge into synthesize_node.
"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents import security_agent, structure_agent


class GraphState(TypedDict, total=False):
    filepath: str
    security_findings: list
    security_summary: str
    structure_findings: list
    structure_summary: str
    final_report: dict


def security_node(state: GraphState) -> GraphState:
    report = security_agent.analyze_file(state["filepath"])
    d = report.to_dict()
    return {"security_findings": d["findings"], "security_summary": d["summary"]}


def structure_node(state: GraphState) -> GraphState:
    report = structure_agent.analyze_file(state["filepath"])
    d = report.to_dict()
    return {"structure_findings": d["findings"], "structure_summary": d["summary"]}


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "unknown": 3}


def synthesize_node(state: GraphState) -> GraphState:
    all_findings = state.get("security_findings", []) + state.get("structure_findings", [])
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "unknown"), 3))

    high = sum(1 for f in all_findings if f.get("severity") == "high")
    medium = sum(1 for f in all_findings if f.get("severity") == "medium")
    low = sum(1 for f in all_findings if f.get("severity") == "low")

    final_report = {
        "file": state["filepath"],
        "totals": {"high": high, "medium": medium, "low": low, "total": len(all_findings)},
        "findings": all_findings,
        "agent_summaries": {
            "security": state.get("security_summary", ""),
            "structure": state.get("structure_summary", ""),
        },
    }
    return {"final_report": final_report}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("security", security_node)
    graph.add_node("structure", structure_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "security")
    graph.add_edge(START, "structure")
    graph.add_edge("security", "synthesize")
    graph.add_edge("structure", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


def run_audit(filepath: str) -> dict:
    app = build_graph()
    result = app.invoke({"filepath": filepath})
    return result["final_report"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m orchestrator.graph <path_to_python_file>")
        sys.exit(1)

    report = run_audit(sys.argv[1])
    print(json.dumps(report, indent=2))
