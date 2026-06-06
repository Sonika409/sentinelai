# SentinelAI — Autonomous Threat Detection Platform

> **FAR AWAY 2026 · Team Zen Hackers · Theme: Agentic & Autonomous Systems**

SentinelAI is a multi-agent AI platform that detects threats autonomously — in **source code** and in **online exams** — without requiring human intervention. Two real-world problems. One agentic engine.

---

## Modules

### 🔍 VulnSentinel — Autonomous Code Security Auditor
Paste any public GitHub URL. A pipeline of five specialised AI agents clones the repository, runs static analysis, maps findings to OWASP Top 10 and CVEs, reasons about real-world exploitability, generates code patches, and produces a full security report — all without a human in the loop.

### 🎓 ExamGuard — AI-Powered Exam Integrity Monitor
A proctoring system that monitors online exams in real time using tab-switch detection, webcam face analysis, and keystroke dynamics. Immediate rule-based alerts fire the moment suspicious behaviour is detected. When the exam ends, a second agent pipeline performs deep behavioural analysis and generates an integrity report with a verdict.

---

## Demo

| VulnSentinel — Live Agent Feed | ExamGuard — Invigilator Dashboard |
|---|---|
| *(screenshot)* | *(screenshot)* |

> 📹 **Demo video:** *(link)*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js 14 Frontend                         │
│   / (home)  ·  /scan  ·  /scan/[id]  ·  /exam/[id]  ·         │
│   /exam/[id]/monitor                                            │
└───────────────────┬─────────────────────────────────────────────┘
                    │  REST + WebSocket
┌───────────────────▼─────────────────────────────────────────────┐
│                  FastAPI Backend  (main.py)                      │
├──────────────────────────┬──────────────────────────────────────┤
│   VulnSentinel           │   ExamGuard                          │
│   POST /api/scan         │   POST /api/exam/session             │
│   WS   /ws/{scan_id}     │   WS   /ws/exam/{id}  (bidir)        │
│   GET  /api/report/{id}  │   POST /api/exam/{id}/analyze        │
│                          │   WS   /ws/exam/{id}/analysis        │
│                          │   GET  /api/exam/report/{id}         │
├──────────────────────────┴──────────────────────────────────────┤
│              LangGraph Agent Pipelines                           │
│                                                                  │
│  VulnSentinel                    ExamGuard                       │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │ orchestrator        │         │ session_monitor      │        │
│  │ → scanner           │         │ → behavior_analyzer  │        │
│  │ → vuln_analyzer     │         │ → anomaly_scorer     │        │
│  │ → exploit_reasoner  │         │ → alert_generator    │        │
│  │ → fix_suggester     │         │ → report_generator   │        │
│  │ → report_generator  │         └─────────────────────┘        │
│  └─────────────────────┘                                         │
│              Powered by Claude claude-sonnet-4-6 API                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Claude claude-sonnet-4-6 (Anthropic API) |
| Backend | Python 3.11 · FastAPI · WebSockets |
| Static analysis | Semgrep · Bandit |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Real-time | Native WebSocket (browser ↔ server) |

---

## Project Structure

```
sentinelai/
├── backend/
│   ├── main.py                     # FastAPI app — all routes & WebSocket endpoints
│   ├── agents/
│   │   ├── state.py                # ScanState TypedDict
│   │   └── orchestrator.py         # VulnSentinel 6-node LangGraph graph
│   ├── exam_agents/
│   │   ├── exam_state.py           # ExamSession TypedDict
│   │   ├── exam_pipeline.py        # ExamGuard 5-node LangGraph graph
│   │   └── event_rules.py          # Rule-based instant alert thresholds
│   ├── tools/
│   │   ├── git_cloner.py           # Repo clone + tech stack detection
│   │   ├── bandit_runner.py        # Python static analysis
│   │   └── semgrep_runner.py       # Multi-language static analysis
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── page.tsx                # Homepage — module selector
    │   ├── scan/
    │   │   ├── page.tsx            # Repo URL input
    │   │   └── [id]/page.tsx       # Live scan dashboard (split-pane)
    │   └── exam/
    │       ├── page.tsx            # Create exam session
    │       ├── [id]/page.tsx       # Student exam view (proctored)
    │       └── [id]/monitor/page.tsx  # Invigilator dashboard
    ├── components/
    │   ├── vulnsentinel/
    │   │   ├── AgentFeed.tsx       # Terminal-style live log stream
    │   │   └── VulnCard.tsx        # Vuln card with collapsible patch diff
    │   └── examguard/
    │       ├── AlertFeed.tsx       # Real-time alert stream
    │       ├── FaceMonitor.tsx     # Webcam feed + face event emitter
    │       └── IntegrityScore.tsx  # Animated circular integrity gauge
    └── lib/
        ├── ws.ts                   # useWebSocket hook
        └── api.ts                  # Typed API client
```

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Semgrep](https://semgrep.dev/docs/getting-started/) — `pip install semgrep`
- [Bandit](https://bandit.readthedocs.io/) — `pip install bandit`
- Anthropic API key → [console.anthropic.com](https://console.anthropic.com)

### 1 — Backend

```bash
cd backend

# Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start server
bash run.sh
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## How It Works

### VulnSentinel — 6-Agent Pipeline

```
User pastes GitHub URL
        │
   [Orchestrator]  Plans scan strategy using LLM reasoning
        │
   [Scanner]       Clones repo · detects tech stack · runs Semgrep + Bandit
        │
   [Vuln Analyzer] Maps raw findings → structured vulnerabilities with OWASP + CVE context
        │
   [Exploit Reasoner]  Explains how each HIGH/CRITICAL vuln can be exploited in the real world
        │
   [Fix Suggester]     Generates code patches for each vulnerability
        │
   [Report Generator]  Compiles executive summary · risk score · full JSON report
        │
   Results streamed live to the browser via WebSocket
```

### ExamGuard — Two-Phase System

**Phase 1 — Real-time (during exam)**
```
Browser detects event (tab switch / face absent / copy-paste)
        │
   WebSocket → event_rules.py
        │
   Rule threshold crossed? → immediate_alert fired to invigilator dashboard instantly
```

**Phase 2 — Deep analysis (after exam ends)**
```
POST /api/exam/{id}/analyze
        │
   [Session Monitor]    Validates session · computes statistics
        │
   [Behavior Analyzer]  LLM identifies suspicious patterns across the full event log
        │
   [Anomaly Scorer]     Scores each category 0–100 for suspicion level
        │
   [Alert Generator]    Produces prioritised, actionable alerts for the invigilator
        │
   [Report Generator]   Integrity score + CLEAN / SUSPICIOUS / FLAGGED verdict + narrative
        │
   Streamed live to invigilator dashboard via WebSocket
```

### Real-time Alert Thresholds (ExamGuard)

| Trigger | Threshold | Severity |
|---------|-----------|----------|
| Tab switches | 3× | WARNING |
| Tab switches | 7× | CRITICAL |
| Face absent | 10 s continuous | WARNING |
| Face absent | 30 s continuous | CRITICAL |
| Multiple faces detected | 2 faces | WARNING |
| Multiple faces detected | 3+ faces | CRITICAL |
| Copy-paste events | 2× | WARNING |
| Copy-paste events | 5× | CRITICAL |

---

## WebSocket Message Protocol

### VulnSentinel (`/ws/{scan_id}`)
```jsonc
// Server → Client
{ "type": "update", "node": "vuln_analyzer", "logs": ["..."], "status": "exploiting", "scan_id": "a1b2c3" }
{ "type": "done",   "scan_id": "a1b2c3", "report": { ... } }
{ "type": "error",  "scan_id": "a1b2c3", "message": "..." }
{ "type": "ping" }
```

### ExamGuard event socket (`/ws/exam/{exam_id}`)
```jsonc
// Client → Server
{ "type": "tab_event",       "event_type": "blur",   "timestamp": 1234567890.0 }
{ "type": "face_event",      "face_count": 0,         "confidence": 0.95, "timestamp": 1234567890.0 }
{ "type": "keystroke_stats", "avg_wpm": 67,            "pause_count": 1, ... }
{ "type": "copy_paste",      "content_length": 342,   "timestamp": 1234567890.0 }
{ "type": "end_exam" }

// Server → Client
{ "type": "immediate_alert", "severity": "CRITICAL", "title": "Multiple Faces Detected", "message": "...", "recommended_action": "..." }
{ "type": "exam_ended" }
```

---

## API Reference

### VulnSentinel

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scan` | Start a scan · returns `scan_id` + `ws_url` |
| `WS` | `/ws/{scan_id}` | Stream real-time agent progress |
| `GET` | `/api/report/{scan_id}` | Fetch completed report |
| `GET` | `/api/scans` | List all scans |

### ExamGuard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/exam/session` | Create exam session · returns `exam_id` |
| `WS` | `/ws/exam/{exam_id}` | Bidirectional event stream |
| `POST` | `/api/exam/{exam_id}/analyze` | Trigger post-session analysis |
| `WS` | `/ws/exam/{exam_id}/analysis` | Stream analysis progress |
| `GET` | `/api/exam/report/{exam_id}` | Fetch integrity report |
| `GET` | `/api/exam/sessions` | List all sessions |

---

## Team

**Team Zen Hackers** — FAR AWAY 2026

| Name | Role |
|------|------|
| Saee Nikam | Team Lead |
| Pushpender Singh | Backend · Agent Pipelines |
| Vaibhav Haval | Frontend · UI/UX |
| Shreya Magadum | ML · Integration |
| Sonika Kaswan | QA · Presentation |

---

## License

MIT — built for FAR AWAY 2026. Not for production use without security review.
