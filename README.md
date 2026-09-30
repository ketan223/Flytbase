# Autonomous Drone Security Analyst Agent
### AI Engineer Technical Assignment — FlytBase

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-9%20passed%20(100%25)-brightgreen.svg)]()
[![Framework](https://img.shields.io/badge/LangChain-Enabled-orange.svg)]()
[![Vector DB](https://img.shields.io/badge/ChromaDB-Active-blueviolet.svg)]()
[![UI](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)]()

> A production-grade prototype for an autonomous **Drone-in-a-Box (DiaB)** security analyst agent. The system ingests synchronized drone telemetry and video frames in real time, applies Vision-Language Model (VLM) reasoning, tracks cross-frame context and recurrence, enforces perimeter security policies, indexes frames for natural language semantic search, and provides conversational security Q&A.

---

## 📑 Table of Contents
1. [Key Features & Highlights](#-key-features--highlights)
2. [Architecture Overview](#-architecture-overview)
3. [Quickstart & Installation](#-quickstart--installation)
4. [Running the Prototype](#-running-the-prototype)
   - [Interactive Streamlit Command Dashboard](#1-interactive-streamlit-command-dashboard-recommended-for-video-recording)
   - [CLI Quick Run](#2-cli-quick-run)
5. [Verification Against Expected Outputs](#-verification-against-expected-outputs)
6. [Automated QA & Test Suite](#-automated-qa--test-suite)
7. [Design Decisions & Trade-Offs](#-design-decisions--trade-offs)
8. [AI-Assisted Workflow Disclosure](#-ai-assisted-workflow-disclosure)
9. [Deliverables & Submission Checklist](#-deliverables--submission-checklist)

---

## 🌟 Key Features & Highlights

- **Multimodal Video & Telemetry Pipeline**: Ingests high-resolution visual frames synchronized with GPS coordinates, altitude (AGL), flight speed, heading, battery state, and property zone metadata.
- **Vision-Language Model (VLM) Reasoning**: Derives dense scene captions, classifies entities (vehicles, pedestrians), and extracts operational attributes (make, model, color, posture).
- **Stateful Context Management**: Tracks objects across frames, calculating continuous dwell times and identifying repeat visits (e.g., *"a blue Ford F150 entered twice today"*).
- **Real-Time Security Rules Engine**: Evaluates safety policies dynamically:
  - `RULE_LOITERING_DETECTED`: Person loitering stationary in access zones (>20s).
  - `RULE_CURFEW_TRESPASS`: After-hours unauthorized human or vehicular activity (22:00 – 06:00).
  - `RULE_REPEAT_VEHICLE_ENTRY`: Multi-visit recurrence tracking.
  - `RULE_EMERGENCY_LANE_OBSTRUCTION`: Fire lane blockage hazards.
- **Cross-Domain Frame Indexing & Search**: Hybrid architecture featuring:
  - **SQLite**: Structured telemetry, frame logs, and immutable security audit records.
  - **ChromaDB**: Semantic vector embeddings enabling natural-language queries (e.g., *"show all truck events"*).
- **Bonus Enhancements Included**:
  - 🎯 **Patrol Video Summarizer**: Generates 1-sentence executive summaries and structured operational debriefs.
  - 🎯 **LangChain Security Analyst Chat**: Conversational tool-calling agent answering follow-up queries (*"What objects were in the video?"*, *"Did anyone loiter at midnight?"*).

---

## 🏗 System Architecture

```
                 ┌────────────────────────────────────────────────┐
                 │       Docked Drone (DiaB / Patrol Sortie)      │
                 │   - Video Stream / Video Frame Sequence        │
                 │   - Real-time GPS, Altitude, Zone HUD          │
                 └───────────────────────┬────────────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │             Vision & VLM Pipeline              │
                 │   - Scene Captions & Fine-Grained Entities     │
                 │   - (BLIP / CLIP / Multimodal Architecture)    │
                 └───────────────────────┬────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
    ┌───────────────────────────────┐         ┌───────────────────────────────┐
    │     Context & State Memory    │         │      Rules & Alert Engine     │
    │  - Cross-frame entity tracking│         │  - Loitering detection (>20s) │
    │  - Visit frequency (visit #2) │         │  - Curfew enforcement (22-06) │
    │  - Zone route history         │         │  - Emergency fire lane block  │
    └───────────────┬───────────────┘         └───────────────┬───────────────┘
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │           Dual Storage & Search Engine         │
                 │  - SQLite: Structured telemetry & alert logs   │
                 │  - ChromaDB: Semantic frame vector embeddings  │
                 └───────────────────────┬────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
    ┌───────────────────────────────┐         ┌───────────────────────────────┐
    │    LangChain Security Agent   │         │     Interactive Web HUD UI    │
    │  - Conversational follow-up   │         │  - Real-time video/telemetry  │
    │  - 1-Sentence auto-summary    │         │  - Alert center & search bar  │
    └───────────────────────────────┘         └───────────────────────────────┘
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Git

### 1. Clone & Setup Environment
```bash
git clone <YOUR_PRIVATE_REPO_URL>
cd AI_Boss

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🎮 Running the Prototype

### 1. Interactive Streamlit Command Dashboard *(Recommended for Video Recording)*
Launch the full tactical security operations dashboard:
```bash
streamlit run dashboard/app.py
```
**Dashboard Features**:
- **📹 Live Patrol HUD & Frames**: Timeline scrubber through video frames with tactical HUD overlay (altitude, battery, GPS coordinates, detection boxes).
- **🚨 Real-Time Security Alerts**: Live alert cards with severity color-coding, rule triggers, and suggested guard actions.
- **🔍 Cross-Domain Semantic Search**: Search bar querying ChromaDB (e.g. type `"show all truck events"` to see matching frames).
- **🤖 LangChain Security Analyst Chat**: Interactive chatbot with pre-built prompt buttons (*"What objects were in the video?"*, *"Did the blue Ford F150 enter twice?"*).
- **📋 Video Summarizer & Debrief**: 1-sentence executive summary and chronological operational logs.

### 2. CLI Quick Run
To run an automated terminal simulation of daytime and midnight patrols with end-to-end logging:
```bash
python run_demo.py
```

---

## 🎯 Verification Against Expected Outputs

| Assignment Requirement | Target Sample Output | Actual System Output | Verification Status |
|---|---|---|---|
| **Operational Log** | `"Blue Ford F150 spotted at garage, 12:00."` | `[LOG] Blue Ford F150 spotted at executive garage, 12:00.` | ✅ **VERIFIED** |
| **Real-Time Alert** | `"Person loitering at main gate, 00:01."` | `[ALERT - CRITICAL] Person loitering at main gate, 00:01. (Rule: RULE_LOITERING_DETECTED)` | ✅ **VERIFIED** |
| **Context Memory** | `"a blue Ford F150 entered twice today"` | `[ALERT - WARNING] Blue Ford F150 entered twice today. (Rule: RULE_REPEAT_VEHICLE_ENTRY)` | ✅ **VERIFIED** |
| **Indexed Frames** | Queryable by object (`"show all truck events"`) | Returns `FRAME_001`, `FRAME_002`, `FRAME_003` with vector similarity scores and imagery | ✅ **VERIFIED** |
| **Bonus 1** | 1-Sentence Video Summary | `"Patrol mission PATROL_NIGHT_0001 completed across 3 zones: 4 security alert(s) triggered, including Person loitering at main gate, 00:01."` | ✅ **VERIFIED** |
| **Bonus 2** | Follow-up Question Answering | Agent answers `"What objects were in the video?"` with complete entity profiles and visit counts | ✅ **VERIFIED** |

---

## 🧪 Automated QA & Test Suite

The test suite validates every module using **pytest**:
```bash
python -m pytest tests/ -v
```

### Test Results Summary:
```text
tests/test_agent_qa.py::test_video_summarizer_bonus PASSED               [ 11%]
tests/test_agent_qa.py::test_agent_follow_up_qa_bonus PASSED             [ 22%]
tests/test_context_and_rules.py::test_truck_logged_correctly PASSED      [ 33%]
tests/test_context_and_rules.py::test_alert_triggered_at_midnight PASSED [ 44%]
tests/test_context_and_rules.py::test_repeat_vehicle_entry_tracking PASSED [ 55%]
tests/test_indexing_search.py::test_sqlite_indexing_and_query PASSED     [ 66%]
tests/test_indexing_search.py::test_chroma_semantic_search_truck_events PASSED [ 77%]
tests/test_telemetry.py::test_drone_telemetry_model PASSED               [ 88%]
tests/test_telemetry.py::test_drone_simulator_stream PASSED              [100%]

======================== 9 passed in 69.11s (100% Pass Rate) ========================
```

---

## ⚖️ Design Decisions & Trade-Offs

### 1. Why CLIP vs. BLIP?
- **BLIP (Generative VLM)**: Excels at free-form, detailed natural language captioning without pre-defining visual labels, making it ideal for descriptive surveillance logging.
- **CLIP (Contrastive Dual-Encoder)**: Excels at cross-modal alignment and rapid similarity ranking, making it ideal for natural-language search across indexed frames.
- **Our Solution**: A **hybrid pipeline** where BLIP-style captioning creates rich textual context, and dense vector embeddings index these records into ChromaDB for sub-second retrieval.

### 2. Relational (SQLite) + Vector (ChromaDB) Dual Store
- **SQLite**: Ensures strict ACID compliance, relational integrity, timestamp filtering, and immutable security audit trails.
- **ChromaDB**: Enables semantic approximate nearest neighbor (ANN) vector search, allowing security guards to use natural queries like *"show all truck events"* without writing SQL.

---

## 🤖 AI-Assisted Workflow Disclosure

In accordance with assignment requirements to leverage AI-assisted tools:
- **Scaffolding & Architecture**: AI assisted in architecting the decoupled Pydantic data contracts and pipeline flow.
- **LangChain Tool Integration**: AI assisted in scaffolding the initial `@tool` classes, which were customized with security policies, dwell-time logic, and conversational fallbacks.
- **Test Generation**: Automated the generation of edge-case test suites (midnight rollover boundaries and visit recurrence).

---

## 📦 Deliverables & Submission Checklist

- [x] **Private GitHub Repository**: Code committed and ready to share.
- [x] **Collaborator Access**: Add `assignments@flytbase.com` as collaborator.
- [x] **Comprehensive README**: Installation, architecture, AI tools disclosure, and verification tables.
- [x] **Detailed Design & Testing Docs**:
  - `docs/FEATURE_SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/TESTING_REPORT.md`
  - `docs/CANDIDATE_REPORT.md`
- [x] **Formal PDF Report**: Generated at `docs/FlytBase_AI_Engineer_Assignment_Report.pdf`.
- [x] **Bonus Enhancements**: Both 1-sentence video summarization and conversational Q&A agent fully implemented.
- [ ] **Demo Video with Voiceover**: Screen record `streamlit run dashboard/app.py` showcasing the tabs and upload to Google Drive.
