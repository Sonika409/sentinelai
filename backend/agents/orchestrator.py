"""
VulnSentinel — LangGraph Orchestrator
Coordinates all security scanning agents in a directed acyclic pipeline.

Graph shape:
  orchestrator → scanner → vuln_analyzer → exploit_reasoner → fix_suggester → report_generator → END
                         ↘                ↘
                       (no findings)   (no vulns)
                               ↘         ↘
                              report_generator → END
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncGenerator, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .state import ScanState

logger = logging.getLogger(__name__)

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _parse_json(text: str, fallback: object) -> object:
    """Strip markdown fences if present, then parse JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("JSON parse failed, using fallback. Raw: %s", text[:200])
        return fallback


def _log(msg: str) -> list[str]:
    logger.info(msg)
    return [msg]


# ══════════════════════════════════════════════════════════════
#  Node: Orchestrator
# ══════════════════════════════════════════════════════════════

def orchestrator_node(state: ScanState) -> dict:
    """Uses LLM to plan the scan strategy before handing off to the scanner."""
    response = llm.invoke([
        SystemMessage(content="""You are a security orchestrator agent.
Given a repository URL, output a JSON scan plan:
{
  "strategy": "brief description of approach",
  "priority_areas": ["list", "of", "focus", "areas"],
  "risk_level": "HIGH|MEDIUM|LOW"
}
Output only valid JSON. No markdown."""),
        HumanMessage(content=f"Plan a security audit for: {state['repo_url']}"),
    ])

    plan = _parse_json(response.content, {
        "strategy": "standard full-repo scan",
        "priority_areas": ["authentication", "input validation", "dependencies"],
        "risk_level": "MEDIUM",
    })

    return {
        "status": "scanning",
        "agent_logs": [
            f"[Orchestrator] Scan {state['scan_id']} started for {state['repo_url']}",
            f"[Orchestrator] Strategy: {plan['strategy']}",
            f"[Orchestrator] Priority areas: {', '.join(plan['priority_areas'])}",
            f"[Orchestrator] Estimated risk level: {plan['risk_level']}",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node: Scanner
# ══════════════════════════════════════════════════════════════

def scanner_node(state: ScanState) -> dict:
    """Clones the repo and runs Semgrep + Bandit static analysis."""
    from tools.git_cloner import clone_repo, detect_tech_stack
    from tools.bandit_runner import run_bandit
    from tools.semgrep_runner import run_semgrep

    try:
        repo_path = clone_repo(state["repo_url"], state["scan_id"])
        tech_stack = detect_tech_stack(repo_path)
        logs = [
            f"[Scanner] Cloned to {repo_path}",
            f"[Scanner] Languages: {', '.join(tech_stack.get('languages', ['unknown']))}",
            f"[Scanner] Dependencies: {len(tech_stack.get('dependencies', []))} found",
        ]

        raw_findings: list[dict] = []

        if "python" in [l.lower() for l in tech_stack.get("languages", [])]:
            bandit_results = run_bandit(repo_path)
            raw_findings.extend(bandit_results)
            logs.append(f"[Scanner] Bandit: {len(bandit_results)} issues")

        semgrep_results = run_semgrep(repo_path)
        raw_findings.extend(semgrep_results)
        logs.append(f"[Scanner] Semgrep: {len(semgrep_results)} issues")
        logs.append(f"[Scanner] Total raw findings: {len(raw_findings)}")

        return {
            "repo_path": repo_path,
            "tech_stack": tech_stack,
            "raw_findings": raw_findings,
            "status": "analyzing",
            "agent_logs": logs,
        }

    except Exception as exc:
        logger.exception("Scanner failed")
        return {
            "errors": [f"Scanner error: {exc}"],
            "status": "error",
            "agent_logs": [f"[Scanner] ERROR: {exc}"],
        }


# ══════════════════════════════════════════════════════════════
#  Node: Vulnerability Analyzer
# ══════════════════════════════════════════════════════════════

def vuln_analyzer_node(state: ScanState) -> dict:
    """Maps raw static-analysis findings to structured Vulnerability objects."""
    findings_json = json.dumps(state["raw_findings"][:25], indent=2)  # cap for token budget

    response = llm.invoke([
        SystemMessage(content="""You are a vulnerability analysis agent.
Map raw static analysis findings to structured vulnerability objects.
Return a JSON array. Each object must have:
{
  "id": "VULN-001",
  "file": "relative/path/to/file.py",
  "line": 42,
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "category": "OWASP label e.g. A03:2021-Injection",
  "description": "clear one-sentence description",
  "cve": "CVE-XXXX-XXXX or null"
}
Output only a valid JSON array. No markdown."""),
        HumanMessage(content=f"Analyze these raw findings:\n{findings_json}"),
    ])

    vulns = _parse_json(response.content, [])

    severity_counts: dict[str, int] = {}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "vulnerabilities": vulns,
        "status": "exploiting",
        "agent_logs": [
            f"[VulnAnalyzer] Mapped {len(vulns)} structured vulnerabilities",
            f"[VulnAnalyzer] Severity breakdown: {severity_counts}",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node: Exploit Reasoner
# ══════════════════════════════════════════════════════════════

def exploit_reasoner_node(state: ScanState) -> dict:
    """Reasons about real-world exploitability for HIGH/CRITICAL vulnerabilities."""
    targets = [v for v in state["vulnerabilities"] if v["severity"] in ("CRITICAL", "HIGH")]

    if not targets:
        return {
            "exploits": [],
            "status": "patching",
            "agent_logs": ["[ExploitReasoner] No HIGH/CRITICAL findings — skipping."],
        }

    response = llm.invoke([
        SystemMessage(content="""You are an exploit reasoning agent.
For each vulnerability explain how an attacker would exploit it.
Return a JSON array. Each object must have:
{
  "vuln_id": "VULN-001",
  "exploitability": "EASY|MODERATE|HARD",
  "attack_vector": "e.g. unauthenticated POST /api/login",
  "impact": "e.g. full database dump",
  "poc_description": "step-by-step attack walkthrough"
}
Output only a valid JSON array. Be specific and technical. No markdown."""),
        HumanMessage(content=f"Reason about exploitability:\n{json.dumps(targets, indent=2)}"),
    ])

    exploits = _parse_json(response.content, [])
    easy = sum(1 for e in exploits if e.get("exploitability") == "EASY")

    return {
        "exploits": exploits,
        "status": "patching",
        "agent_logs": [
            f"[ExploitReasoner] Analyzed {len(exploits)} critical/high vulnerabilities",
            f"[ExploitReasoner] {easy} are trivially exploitable (EASY)",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node: Fix Suggester
# ══════════════════════════════════════════════════════════════

def fix_suggester_node(state: ScanState) -> dict:
    """Generates code patches for CRITICAL, HIGH, and MEDIUM vulnerabilities."""
    targets = [v for v in state["vulnerabilities"] if v["severity"] in ("CRITICAL", "HIGH", "MEDIUM")]

    if not targets:
        return {
            "patches": [],
            "status": "reporting",
            "agent_logs": ["[FixSuggester] Nothing to patch."],
        }

    patches = []
    logs = []

    for vuln in targets:
        response = llm.invoke([
            SystemMessage(content="""You are a secure code fix agent.
Generate a targeted code patch for the vulnerability provided.
Return a single JSON object:
{
  "vuln_id": "VULN-001",
  "file": "path/to/file.py",
  "original_code": "the vulnerable snippet",
  "patched_code": "the fixed snippet",
  "explanation": "what changed and why it fixes the vulnerability"
}
Output only valid JSON. No markdown."""),
            HumanMessage(content=f"Fix this vulnerability:\n{json.dumps(vuln, indent=2)}"),
        ])

        patch = _parse_json(response.content, None)
        if patch:
            patches.append(patch)
            logs.append(f"[FixSuggester] Patch ready for {vuln['id']} — {vuln['severity']}")
        else:
            logs.append(f"[FixSuggester] Could not generate patch for {vuln['id']}")

    logs.append(f"[FixSuggester] {len(patches)}/{len(targets)} patches generated")

    return {
        "patches": patches,
        "status": "reporting",
        "agent_logs": logs,
    }


# ══════════════════════════════════════════════════════════════
#  Node: Report Generator
# ══════════════════════════════════════════════════════════════

def report_generator_node(state: ScanState) -> dict:
    """Compiles all agent outputs into the final structured report."""
    critical = [v for v in state.get("vulnerabilities", []) if v["severity"] == "CRITICAL"]
    high = [v for v in state.get("vulnerabilities", []) if v["severity"] == "HIGH"]

    response = llm.invoke([
        SystemMessage(content="""You are a security report writer.
Produce an executive summary for a security audit.
Return a JSON object:
{
  "executive_summary": "2-3 sentences for a non-technical stakeholder",
  "risk_score": <integer 0-100>,
  "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW",
  "key_recommendations": ["top 3 action items, ordered by priority"]
}
Output only valid JSON. No markdown."""),
        HumanMessage(content=f"""Repository: {state['repo_url']}
Tech stack: {state.get('tech_stack', {})}
Total vulnerabilities: {len(state.get('vulnerabilities', []))}
Critical: {len(critical)}, High: {len(high)}
Top findings: {json.dumps(state.get('vulnerabilities', [])[:5], indent=2)}"""),
    ])

    summary = _parse_json(response.content, {
        "executive_summary": "Security scan completed. Review findings for details.",
        "risk_score": 50,
        "overall_risk": "MEDIUM",
        "key_recommendations": ["Review and patch all CRITICAL and HIGH findings immediately."],
    })

    report = {
        "scan_id": state["scan_id"],
        "repo_url": state["repo_url"],
        "tech_stack": state.get("tech_stack", {}),
        "summary": summary,
        "vulnerabilities": state.get("vulnerabilities", []),
        "exploits": state.get("exploits", []),
        "patches": state.get("patches", []),
        "total_findings": len(state.get("vulnerabilities", [])),
        "errors": state.get("errors", []),
    }

    return {
        "report": report,
        "status": "done",
        "agent_logs": [
            f"[ReportGenerator] Risk score: {summary['risk_score']}/100",
            f"[ReportGenerator] Overall risk: {summary['overall_risk']}",
            f"[ReportGenerator] Scan {state['scan_id']} complete.",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Conditional routing
# ══════════════════════════════════════════════════════════════

def _route_after_scanner(state: ScanState) -> Literal["vuln_analyzer", "report_generator"]:
    if state.get("errors") or not state.get("raw_findings"):
        return "report_generator"
    return "vuln_analyzer"


def _route_after_vuln_analyzer(state: ScanState) -> Literal["exploit_reasoner", "report_generator"]:
    if not state.get("vulnerabilities"):
        return "report_generator"
    return "exploit_reasoner"


# ══════════════════════════════════════════════════════════════
#  Graph assembly
# ══════════════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    graph = StateGraph(ScanState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("scanner", scanner_node)
    graph.add_node("vuln_analyzer", vuln_analyzer_node)
    graph.add_node("exploit_reasoner", exploit_reasoner_node)
    graph.add_node("fix_suggester", fix_suggester_node)
    graph.add_node("report_generator", report_generator_node)

    graph.set_entry_point("orchestrator")

    graph.add_edge("orchestrator", "scanner")
    graph.add_conditional_edges("scanner", _route_after_scanner, {
        "vuln_analyzer": "vuln_analyzer",
        "report_generator": "report_generator",
    })
    graph.add_conditional_edges("vuln_analyzer", _route_after_vuln_analyzer, {
        "exploit_reasoner": "exploit_reasoner",
        "report_generator": "report_generator",
    })
    graph.add_edge("exploit_reasoner", "fix_suggester")
    graph.add_edge("fix_suggester", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile(checkpointer=MemorySaver())


_graph = build_graph()


# ══════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════

def _initial_state(repo_url: str, scan_id: Optional[str] = None) -> ScanState:
    sid = scan_id or str(uuid.uuid4())[:8]
    return ScanState(
        repo_url=repo_url,
        scan_id=sid,
        repo_path="",
        tech_stack={},
        raw_findings=[],
        vulnerabilities=[],
        exploits=[],
        patches=[],
        report={},
        status="starting",
        errors=[],
        agent_logs=[f"[Orchestrator] Initializing scan {sid} for {repo_url}"],
    )


async def run_scan(repo_url: str, scan_id: Optional[str] = None) -> ScanState:
    """Run a full scan and return the completed state."""
    state = _initial_state(repo_url, scan_id)
    config = {"configurable": {"thread_id": state["scan_id"]}}
    return await _graph.ainvoke(state, config=config)


async def stream_scan(repo_url: str, scan_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
    """Yield node-by-node updates for WebSocket streaming to the frontend."""
    state = _initial_state(repo_url, scan_id)
    config = {"configurable": {"thread_id": state["scan_id"]}}

    async for event in _graph.astream(state, config=config):
        node_name, node_output = next(iter(event.items()))
        yield {
            "node": node_name,
            "logs": node_output.get("agent_logs", []),
            "status": node_output.get("status", ""),
            "scan_id": state["scan_id"],
        }
