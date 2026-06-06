"""
ExamGuard — shared state schema.
All events originate in the browser and arrive via WebSocket before
the LangGraph pipeline runs its post-session analysis.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


# ── Raw browser events ────────────────────────────────────────

class TabEvent(TypedDict):
    timestamp: float
    event_type: str       # "blur" | "focus" | "hidden" | "visible"

class FaceEvent(TypedDict):
    timestamp: float
    face_count: int       # 0 = absent, 1 = normal, 2+ = multiple people
    confidence: float     # model confidence 0.0–1.0

class KeystrokeStats(TypedDict):
    avg_wpm: float
    std_wpm: float        # high std = burst typing → suspicious
    pause_count: int      # pauses longer than 3 s
    burst_count: int      # runs of >120 wpm
    total_keystrokes: int

class CopyPasteEvent(TypedDict):
    timestamp: float
    content_length: int   # chars pasted


# ── Agent outputs ─────────────────────────────────────────────

class BehaviorFlag(TypedDict):
    flag_id: str
    timestamp: float
    category: str         # TAB_SWITCH | FACE_ABSENT | MULTIPLE_FACES
                          # UNUSUAL_TYPING | COPY_PASTE | FOCUS_LOSS
    severity: str         # HIGH | MEDIUM | LOW
    description: str
    evidence: List[str]   # raw data points that triggered this flag

class AnomalyScore(TypedDict):
    category: str
    score: float          # 0–100  (0 = perfectly clean, 100 = definite cheat)
    reasoning: str

class Alert(TypedDict):
    alert_id: str
    timestamp: float
    severity: str         # CRITICAL | WARNING | INFO
    title: str
    message: str
    recommended_action: str


# ── Full session state (flows through LangGraph) ──────────────

class ExamSession(TypedDict):
    # ── Identity ───────────────────────────────────────────
    exam_id: str
    student_id: str
    student_name: str
    exam_name: str
    duration_minutes: int
    started_at: float
    ended_at: Optional[float]

    # ── Raw browser events ─────────────────────────────────
    tab_events: List[TabEvent]
    face_events: List[FaceEvent]
    keystroke_stats: Optional[KeystrokeStats]
    copy_paste_events: List[CopyPasteEvent]

    # ── Immediate rule-based alerts (fired live) ───────────
    immediate_alerts: List[dict]

    # ── LangGraph agent outputs ────────────────────────────
    behavior_flags: List[BehaviorFlag]
    anomaly_scores: List[AnomalyScore]
    alerts: List[Alert]

    # ── Final verdict ──────────────────────────────────────
    integrity_score: float    # 0–100  (100 = fully clean)
    verdict: str              # CLEAN | SUSPICIOUS | FLAGGED
    report: Dict[str, Any]

    # ── Control ────────────────────────────────────────────
    status: str               # active | ended | analyzing | done | error
    errors: List[str]
    agent_logs: Annotated[List[str], operator.add]
