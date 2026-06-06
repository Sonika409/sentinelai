"""
ExamGuard — LangGraph post-session analysis pipeline.

Runs after the exam ends (or on demand) against the accumulated
event log collected in real-time via WebSocket.

Graph shape:
  session_monitor → behavior_analyzer → anomaly_scorer → alert_generator → report_generator → END
                                      ↘ (no flags)
                                      report_generator → END
"""

from __future__ import annotations

import json
import logging
import time
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .exam_state import ExamSession

logger = logging.getLogger(__name__)

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)


# ══════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════

def _parse_json(text: str, fallback: object) -> object:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("JSON parse failed. Raw: %s", text[:200])
        return fallback


# ══════════════════════════════════════════════════════════════
#  Node 1 — Session Monitor
#  Validates the session data and computes summary statistics
#  before handing off to the LLM agents.
# ══════════════════════════════════════════════════════════════

def session_monitor_node(state: ExamSession) -> dict:
    tab_events   = state.get("tab_events", [])
    face_events  = state.get("face_events", [])
    cp_events    = state.get("copy_paste_events", [])
    ks           = state.get("keystroke_stats") or {}

    tab_blur_count    = sum(1 for e in tab_events if e["event_type"] in ("blur", "hidden"))
    absent_face_count = sum(1 for e in face_events if e["face_count"] == 0)
    multi_face_count  = sum(1 for e in face_events if e["face_count"] > 1)
    duration_min      = (
        ((state.get("ended_at") or time.time()) - state["started_at"]) / 60
    )

    logs = [
        f"[SessionMonitor] Exam: {state['exam_name']} | Student: {state['student_name']}",
        f"[SessionMonitor] Duration: {duration_min:.1f} min",
        f"[SessionMonitor] Tab switches (blur): {tab_blur_count}",
        f"[SessionMonitor] Face absent events: {absent_face_count}",
        f"[SessionMonitor] Multiple-face events: {multi_face_count}",
        f"[SessionMonitor] Copy-paste events: {len(cp_events)}",
        f"[SessionMonitor] Avg WPM: {ks.get('avg_wpm', 'N/A')}  |  Pauses: {ks.get('pause_count', 'N/A')}",
    ]

    if tab_blur_count == 0 and absent_face_count == 0 and multi_face_count == 0 and not cp_events:
        logs.append("[SessionMonitor] No suspicious signals detected in raw data.")

    return {
        "status": "analyzing",
        "agent_logs": logs,
    }


# ══════════════════════════════════════════════════════════════
#  Node 2 — Behavior Analyzer
#  LLM identifies patterns across the full event log and
#  produces structured BehaviorFlag objects.
# ══════════════════════════════════════════════════════════════

def behavior_analyzer_node(state: ExamSession) -> dict:
    tab_events  = state.get("tab_events", [])
    face_events = state.get("face_events", [])
    cp_events   = state.get("copy_paste_events", [])
    ks          = state.get("keystroke_stats") or {}

    # Summarise for the LLM (avoid sending thousands of raw events)
    tab_blur_times = [e["timestamp"] for e in tab_events if e["event_type"] in ("blur", "hidden")]
    absent_windows = _compute_absence_windows(face_events)
    multi_face_ts  = [e["timestamp"] for e in face_events if e["face_count"] > 1]

    summary = {
        "exam_name":        state["exam_name"],
        "student_name":     state["student_name"],
        "duration_minutes": (state.get("ended_at", time.time()) - state["started_at"]) / 60,
        "tab_blur_timestamps":     tab_blur_times[:50],
        "face_absent_windows_sec": absent_windows[:20],
        "multiple_face_timestamps": multi_face_ts[:20],
        "copy_paste_count":         len(cp_events),
        "keystroke_stats":          ks,
    }

    response = llm.invoke([
        SystemMessage(content="""You are an exam integrity behavior analysis agent.
Analyze the session summary and identify suspicious behavioral patterns.
Return a JSON array of BehaviorFlag objects, each with:
{
  "flag_id": "FLAG-001",
  "timestamp": <epoch float of when pattern started or peaked>,
  "category": "TAB_SWITCH|FACE_ABSENT|MULTIPLE_FACES|UNUSUAL_TYPING|COPY_PASTE|FOCUS_LOSS",
  "severity": "HIGH|MEDIUM|LOW",
  "description": "one clear sentence describing the suspicious behavior",
  "evidence": ["specific data points that triggered this flag"]
}
Return an empty array [] if the session looks clean.
Output only valid JSON. No markdown."""),
        HumanMessage(content=f"Analyze this exam session:\n{json.dumps(summary, indent=2)}"),
    ])

    flags = _parse_json(response.content, [])

    by_severity = {}
    for f in flags:
        s = f.get("severity", "?")
        by_severity[s] = by_severity.get(s, 0) + 1

    return {
        "behavior_flags": flags,
        "status": "scoring",
        "agent_logs": [
            f"[BehaviorAnalyzer] {len(flags)} behavioral flags raised",
            f"[BehaviorAnalyzer] Breakdown: {by_severity}",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node 3 — Anomaly Scorer
#  Assigns a 0–100 suspicion score per category, with reasoning.
# ══════════════════════════════════════════════════════════════

def anomaly_scorer_node(state: ExamSession) -> dict:
    flags = state.get("behavior_flags", [])

    if not flags:
        return {
            "anomaly_scores": [],
            "status": "alerting",
            "agent_logs": ["[AnomalyScorer] No flags to score."],
        }

    response = llm.invoke([
        SystemMessage(content="""You are an exam anomaly scoring agent.
For each behavioral flag category present, assign a suspicion score.
Return a JSON array:
{
  "category": "TAB_SWITCH",
  "score": 0-100,
  "reasoning": "why this score was assigned"
}
Score meaning: 0=completely clean, 100=almost certainly cheating.
Consider frequency, timing, duration, and context.
Output only valid JSON array. No markdown."""),
        HumanMessage(content=f"Score these behavioral flags:\n{json.dumps(flags, indent=2)}"),
    ])

    scores = _parse_json(response.content, [])
    avg    = sum(s.get("score", 0) for s in scores) / len(scores) if scores else 0

    return {
        "anomaly_scores": scores,
        "status": "alerting",
        "agent_logs": [
            f"[AnomalyScorer] Scored {len(scores)} categories",
            f"[AnomalyScorer] Average suspicion score: {avg:.1f}/100",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node 4 — Alert Generator
#  Translates scores + flags into actionable, prioritised alerts
#  for the invigilator dashboard.
# ══════════════════════════════════════════════════════════════

def alert_generator_node(state: ExamSession) -> dict:
    flags  = state.get("behavior_flags", [])
    scores = state.get("anomaly_scores", [])

    if not flags and not scores:
        return {
            "alerts": [],
            "status": "reporting",
            "agent_logs": ["[AlertGenerator] Nothing to alert."],
        }

    response = llm.invoke([
        SystemMessage(content="""You are an exam integrity alert generation agent.
Convert behavioral flags and anomaly scores into prioritised invigilator alerts.
Return a JSON array ordered by severity (CRITICAL first):
{
  "alert_id": "ALERT-001",
  "timestamp": <epoch float>,
  "severity": "CRITICAL|WARNING|INFO",
  "title": "short title (5 words max)",
  "message": "clear sentence describing the issue for the invigilator",
  "recommended_action": "what the invigilator should do now"
}
Only raise CRITICAL for clear cheating evidence. Use WARNING for suspicious patterns.
Output only valid JSON array. No markdown."""),
        HumanMessage(content=f"""Flags:\n{json.dumps(flags, indent=2)}
\nScores:\n{json.dumps(scores, indent=2)}"""),
    ])

    alerts   = _parse_json(response.content, [])
    critical = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
    warnings = sum(1 for a in alerts if a.get("severity") == "WARNING")

    return {
        "alerts": alerts,
        "status": "reporting",
        "agent_logs": [
            f"[AlertGenerator] {len(alerts)} alerts generated",
            f"[AlertGenerator] CRITICAL: {critical}  |  WARNING: {warnings}",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Node 5 — Report Generator
#  Compiles the final integrity report and overall verdict.
# ══════════════════════════════════════════════════════════════

def report_generator_node(state: ExamSession) -> dict:
    flags   = state.get("behavior_flags", [])
    scores  = state.get("anomaly_scores", [])
    alerts  = state.get("alerts", [])

    avg_score = (
        sum(s.get("score", 0) for s in scores) / len(scores)
        if scores else 0.0
    )
    integrity_score = round(100 - avg_score, 1)

    if integrity_score >= 85:
        verdict = "CLEAN"
    elif integrity_score >= 55:
        verdict = "SUSPICIOUS"
    else:
        verdict = "FLAGGED"

    response = llm.invoke([
        SystemMessage(content="""You are an exam integrity report writer.
Write a concise report for an academic integrity officer.
Return JSON:
{
  "summary": "2-3 sentence overview of what happened during the exam",
  "key_concerns": ["ordered list of the most serious concerns"],
  "timeline_highlights": ["3-5 notable moments with approximate timestamps"],
  "recommendation": "clear recommended action for the institution"
}
Output only valid JSON. No markdown."""),
        HumanMessage(content=f"""Student: {state['student_name']}
Exam: {state['exam_name']}
Integrity score: {integrity_score}/100
Verdict: {verdict}
Flags: {json.dumps(flags[:10], indent=2)}
Alerts: {json.dumps(alerts[:5], indent=2)}"""),
    ])

    narrative = _parse_json(response.content, {
        "summary": "Exam session analysis complete.",
        "key_concerns": [],
        "timeline_highlights": [],
        "recommendation": "Review flagged events manually.",
    })

    report = {
        "exam_id":         state["exam_id"],
        "student_id":      state["student_id"],
        "student_name":    state["student_name"],
        "exam_name":       state["exam_name"],
        "integrity_score": integrity_score,
        "verdict":         verdict,
        "narrative":       narrative,
        "behavior_flags":  flags,
        "anomaly_scores":  scores,
        "alerts":          alerts,
        "immediate_alerts": state.get("immediate_alerts", []),
        "raw_stats": {
            "tab_blur_count":  sum(1 for e in state.get("tab_events", []) if e["event_type"] in ("blur","hidden")),
            "face_absent_count": sum(1 for e in state.get("face_events", []) if e["face_count"] == 0),
            "multi_face_count":  sum(1 for e in state.get("face_events", []) if e["face_count"] > 1),
            "copy_paste_count":  len(state.get("copy_paste_events", [])),
            "keystroke_stats":   state.get("keystroke_stats"),
        },
    }

    verdict_emoji = {"CLEAN": "✅", "SUSPICIOUS": "⚠️", "FLAGGED": "🚨"}.get(verdict, "")

    return {
        "integrity_score": integrity_score,
        "verdict":         verdict,
        "report":          report,
        "status":          "done",
        "agent_logs": [
            f"[ReportGenerator] Integrity score: {integrity_score}/100",
            f"[ReportGenerator] Verdict: {verdict_emoji} {verdict}",
            f"[ReportGenerator] Report ready for {state['student_name']}",
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Routing
# ══════════════════════════════════════════════════════════════

def _route_after_behavior(
    state: ExamSession,
) -> Literal["anomaly_scorer", "report_generator"]:
    if not state.get("behavior_flags"):
        return "report_generator"
    return "anomaly_scorer"


# ══════════════════════════════════════════════════════════════
#  Graph assembly
# ══════════════════════════════════════════════════════════════

def build_exam_graph() -> StateGraph:
    graph = StateGraph(ExamSession)

    graph.add_node("session_monitor",    session_monitor_node)
    graph.add_node("behavior_analyzer",  behavior_analyzer_node)
    graph.add_node("anomaly_scorer",     anomaly_scorer_node)
    graph.add_node("alert_generator",    alert_generator_node)
    graph.add_node("report_generator",   report_generator_node)

    graph.set_entry_point("session_monitor")

    graph.add_edge("session_monitor", "behavior_analyzer")
    graph.add_conditional_edges(
        "behavior_analyzer",
        _route_after_behavior,
        {"anomaly_scorer": "anomaly_scorer", "report_generator": "report_generator"},
    )
    graph.add_edge("anomaly_scorer",    "alert_generator")
    graph.add_edge("alert_generator",   "report_generator")
    graph.add_edge("report_generator",  END)

    return graph.compile(checkpointer=MemorySaver())


_exam_graph = build_exam_graph()


# ══════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════

async def run_exam_analysis(session: ExamSession) -> ExamSession:
    """Run full post-session pipeline; returns completed ExamSession."""
    config = {"configurable": {"thread_id": session["exam_id"]}}
    return await _exam_graph.ainvoke(session, config=config)


async def stream_exam_analysis(session: ExamSession):
    """Yield per-node progress dicts for WebSocket streaming."""
    config = {"configurable": {"thread_id": session["exam_id"]}}
    async for event in _exam_graph.astream(session, config=config):
        node_name, node_output = next(iter(event.items()))
        yield {
            "type":    "analysis_update",
            "node":    node_name,
            "logs":    node_output.get("agent_logs", []),
            "status":  node_output.get("status", ""),
            "exam_id": session["exam_id"],
        }


# ══════════════════════════════════════════════════════════════
#  Utilities
# ══════════════════════════════════════════════════════════════

def _compute_absence_windows(face_events: list) -> list[float]:
    """Return list of consecutive-absent durations in seconds."""
    windows = []
    absent_since: float | None = None
    for ev in sorted(face_events, key=lambda e: e["timestamp"]):
        if ev["face_count"] == 0 and absent_since is None:
            absent_since = ev["timestamp"]
        elif ev["face_count"] > 0 and absent_since is not None:
            windows.append(ev["timestamp"] - absent_since)
            absent_since = None
    return windows
