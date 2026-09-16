"""Shared data structures used across all agents and the orchestrator."""

from dataclasses import dataclass, field, asdict


@dataclass
class Finding:
    line: int
    severity: str          # "low" | "medium" | "high"
    confidence: str        # "low" | "medium" | "high"
    category: str
    description: str
    source: str             # which agent/tool produced this: "bandit", "structure", "llm"


@dataclass
class AgentReport:
    agent: str              # "security" | "structure"
    file: str
    findings: list = field(default_factory=list)   # list[dict], from asdict(Finding)
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
