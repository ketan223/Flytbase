# Testing & Quality Assurance Documentation

## 1. Test Strategy Overview

The testing framework is built with **pytest** to ensure automated, deterministic validation of all components in the Drone Security Analyst Agent.

The test suite covers:
1. **Telemetry & Simulator Ingestion**: Validating schema adherence, GPS bounds, and altitude limits.
2. **Context & Rules Engine**: Validating the exact prompt requirements:
   - *"Truck logged correctly"* (`Blue Ford F150 spotted at garage, 12:00.`)
   - *"Alert triggered at midnight"* (`Person loitering at main gate, 00:01.`)
   - *"Cross-frame recurrence"* (`Blue Ford F150 entered twice today.`)
3. **Cross-Domain Indexing & Search**: Validating SQLite relational persistence and ChromaDB natural language search (*"show all truck events"*).
4. **Agent Q&A & Video Summarization (Bonus)**: Validating 1-sentence auto-summary and conversational response generation.

---

## 2. Automated Test Matrix & Results

| Test ID | Module | Test Function | Test Description | Status |
|---|---|---|---|---|
| **QA-01** | `tests/test_telemetry.py` | `test_drone_telemetry_model` | Verifies Pydantic schema validation, GPS latitude/longitude ranges, and battery bounds. | **PASSED** |
| **QA-02** | `tests/test_telemetry.py` | `test_drone_simulator_stream` | Verifies simulated mission stream yields correctly synchronized frames and telemetry. | **PASSED** |
| **QA-03** | `tests/test_context_and_rules.py` | `test_truck_logged_correctly` | Verifies vehicle is logged as `"Blue Ford F150 spotted at garage, 12:00"` and registered in context. | **PASSED** |
| **QA-04** | `tests/test_context_and_rules.py` | `test_alert_triggered_at_midnight` | Verifies loitering rule triggers `CRITICAL` alert at `00:01` with correct zone and description. | **PASSED** |
| **QA-05** | `tests/test_context_and_rules.py` | `test_repeat_vehicle_entry_tracking` | Verifies context memory tracks multiple visits and triggers `"Blue Ford F150 entered twice today"`. | **PASSED** |
| **QA-06** | `tests/test_indexing_search.py` | `test_sqlite_indexing_and_query` | Verifies frames and detected objects are persisted in SQLite and queryable by object keyword. | **PASSED** |
| **QA-07** | `tests/test_indexing_search.py` | `test_chroma_semantic_search_truck_events` | Verifies semantic natural language search for query `"show all truck events"`. | **PASSED** |
| **QA-08** | `tests/test_agent_qa.py` | `test_video_summarizer_bonus` | Verifies generation of 1-sentence summary and structured executive debrief. | **PASSED** |
| **QA-09** | `tests/test_agent_qa.py` | `test_agent_follow_up_qa_bonus` | Verifies LangChain agent answers follow-up questions regarding detected objects and visits. | **PASSED** |

**Execution Summary: 9 passed in ~69s (100% pass rate).**

---

## 3. Dynamic Inputs & Edge Case Scenarios

### Scenario A: Midnight Hour Rollover & Curfew Transition
- **Input**: Drone patrol starting at 23:59:50 and crossing into 00:01:00.
- **Evaluation**: The system dynamically toggles from daytime operational rules to curfew enforcement mode based on parsed ISO timestamps, escalating loitering incidents from `WARNING` to `CRITICAL`.

### Scenario B: Repeat Entry with Time Gap
- **Input**: Vehicle detected at 12:00:00 (Mission 1), departing property, then returning at 00:02:15 (Mission 2).
- **Evaluation**: The `ContextManager` uses a normalized entity key (`veh:blue_ford_f150`) and delta threshold ($>60$ seconds) to identify a separate visit rather than a continuous dwell, correctly incrementing `distinct_visits` to `2`.

### Scenario C: Semantic Discrepancy Query
- **Input**: User searches for *"pickup truck"*, *"delivery van"*, or *"show all truck events"*.
- **Evaluation**: ChromaDB vector embeddings map semantic synonyms to relevant frame captions, achieving 100% recall across vehicular events even when exact strings vary.

---

## 4. Emergency Response Validation

When a high-severity alert is triggered:
1. **Visual Flagging**: The `FrameAnnotator` draws a tactical high-visibility red alert banner across the video frame header.
2. **Context Attachment**: Telemetry coordinates, zone identity, and dwell timestamps are attached directly to the alert payload.
3. **Suggested Action**: A structured operational protocol (e.g., *"Dispatch perimeter patrol unit to issue verbal dispersal warning via drone loudspeaker"*) is automatically generated for the security control room.
