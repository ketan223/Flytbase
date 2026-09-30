# System Architecture & Design Specification

## 1. High-Level Architecture Overview

The **FlytBase Drone Security Analyst Agent** is structured into five decoupled, modular subsystems:
1. **Telemetry & Visual Ingestion Pipeline**: Ingests synchronized drone telemetry and video frames.
2. **Vision-Language Model (VLM) & Visual Processing**: Computes dense frame captions, detects entities, and extracts semantic attributes.
3. **Temporal Context & State Manager**: Maintains stateful memory of observed objects, dwell times, and recurrence across patrols.
4. **Security Policy & Rules Engine**: Evaluates contextual detections against physical security rules and dispatches alerts.
5. **Dual Storage & Cross-Domain Indexing**: Combines relational storage (SQLite) with semantic vector indexing (ChromaDB) for natural language retrieval and auditability.
6. **Conversational Agent & Summarizer (Bonus)**: Implements LangChain tool-calling agents and post-patrol video summarizers.

```
                              ┌──────────────────────────────────────────┐
                              │     Docked Drone (DiaB Patrol Sortie)    │
                              │  - Video Stream / Video Frame Sequence   │
                              │  - Real-time GPS, Altitude, Zone HUD     │
                              └─────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                              ┌──────────────────────────────────────────┐
                              │         Ingestion & Validation           │
                              │  (DroneMissionSimulator / Frame Stream)  │
                              └─────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                              ┌──────────────────────────────────────────┐
                              │          Vision & VLM Analysis           │
                              │     (BLIP / CLIP / Multimodal VLM)       │
                              │  - Scene Caption & Entity Extraction     │
                              └─────────────────────┬────────────────────┘
                                                    │
                               ┌────────────────────┴────────────────────┐
                               ▼                                         ▼
               ┌───────────────────────────────┐         ┌───────────────────────────────┐
               │    Context & State Manager    │         │     Security Rules Engine     │
               │  - Object Recurrence Tracking │         │  - Loitering Threshold (20s)  │
               │  - Dwell Time Accumulation    │         │  - Curfew Window Enforcement  │
               │  - Zone Trajectory History    │         │  - Emergency Zone Obstruction │
               └───────────────┬───────────────┘         └───────────────┬───────────────┘
                               │                                         │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                              ┌──────────────────────────────────────────┐
                              │       Dual Storage & Indexing Engine     │
                              ├─────────────────────┬────────────────────┤
                              │    SQLite Relational│    ChromaDB Vector │
                              │    Telemetry, Alerts│    Frame Semantic  │
                              │    & Entity Records │    Embeddings      │
                              └─────────────────────┴────────────────────┘
                                                    │
                               ┌────────────────────┴────────────────────┐
                               ▼                                         ▼
               ┌───────────────────────────────┐         ┌───────────────────────────────┐
               │    LangChain Q&A Assistant    │         │      Interactive Dashboard    │
               │  - Tool-Calling Reasoning     │         │  - Live Tactical Drone HUD    │
               │  - Follow-up Property Q&A     │         │  - Real-Time Alerts Dispatch  │
               │  - 1-Sentence Auto-Summary    │         │  - Semantic Frame Search Bar  │
               └───────────────────────────────┘         └───────────────────────────────┘
```

---

## 2. Technical Justification & Trade-off Analysis

### 2.1 VLM Selection: Why CLIP vs. BLIP?

| Dimension | OpenAI CLIP (`clip-vit-base-patch32`) | Salesforce BLIP (`blip-image-captioning-base`) | Selected Approach in Prototype |
|---|---|---|---|
| **Architecture** | Contrastive Dual-Encoder (Image + Text Embeddings) | Encoder-Decoder Generative Vision-Language Model | **Hybrid Multimodal Strategy** |
| **Primary Strength** | Unmatched zero-shot classification and semantic cross-modal vector search. | Direct generative natural language description of unseen scenes without predefined labels. | **BLIP for Captioning & Logging + CLIP/ChromaDB for Vector Indexing**. |
| **Output Type** | Dot-product similarity scores & dense embedding vectors ($512$ dim). | Free-form natural language strings (`"Blue Ford F150 parked at garage"`). | Frame captions are generated via BLIP generative logic, while frame embeddings are indexed via ChromaDB for semantic search. |
| **Resource Footprint** | Extremely lightweight; fast CPU/edge inference. | Moderate memory footprint; requires autoregressive token generation. | Includes lightweight edge-optimized fallback to ensure 0-second cold start and zero latency spikes during live patrols. |

### 2.2 Agent Architecture: Why Tool-Calling with LangChain?

Rather than hardcoding rigid SQL query scripts, the agent uses **LangChain Tool Calling**:
1. **SearchFramesTool**: Translates natural language questions like *"Show all truck events"* into dense vector queries executed against ChromaDB.
2. **QueryAlertsTool**: Queries high-priority security breaches from the SQLite database.
3. **EntityHistoryTool**: Accesses the stateful `ContextManager` to retrieve exact dwell times and visit recurrence (*"The Blue Ford F150 entered for visit #2 today"*).
4. **Modularity & Scalability**: New tools (e.g., PTZ camera zoom, acoustic gunshot sensor, dock battery scheduler) can be plugged in without rewriting prompt chains.

---

## 3. Data Pipeline & Storage Schema

### 3.1 Relational Storage (SQLite: `drone_security.db`)
- `missions`: Stores mission lifecycle, status, timestamps, and executive debriefs.
- `frames`: Stores synchronized telemetry (`altitude_m`, `latitude`, `longitude`, `zone_id`, `zone_name`), visual file references, captions, and alert flags.
- `detected_objects`: Normalized entity detections with confidence scores, labels, and bounding boxes.
- `alerts`: Immutable audit log of security violations, severity levels (`CRITICAL`, `WARNING`, `INFO`), and recommended actions.

### 3.2 Vector Storage (ChromaDB: `drone_surveillance_frames`)
- Document structure:
  ```
  Frame FRAME_001 captured at 2026-09-30 12:00:00.
  Zone: Main Gate. Altitude: 16.5m.
  Caption: A blue Ford F150 pickup truck approaching the Main Gate entrance barrier.
  Detected Objects: vehicle (Blue Ford F150).
  Activity: Authorized commercial entry during operational hours.
  ```
- Metadata attributes: `frame_id`, `mission_id`, `timestamp`, `zone_name`, `altitude_m`, `is_alert`, `has_vehicle`, `has_person`.
- Enables hybrid filtering (e.g., vector search restricted to `where={"has_vehicle": 1}`).

---

## 4. Security Rules & Temporal Reasoning Logic

1. **Loitering Detection Policy**:
   $$\text{Dwell Time} = t_{\text{current}} - t_{\text{first\_seen\_in\_zone}}$$
   If $\text{Dwell Time} \ge 20\text{ seconds}$ and subject is classified as `person` in restricted access zones $\rightarrow$ Dispatch `RULE_LOITERING_DETECTED` alert.
2. **Curfew Violation Policy**:
   Curfew active between 22:00 and 06:00. Any human detected on premises during this window triggers immediate `CRITICAL` severity notification.
3. **Repeat Vehicle Recurrence Policy**:
   If $\text{Distinct Visits Today} \ge 2$ for non-commercial or unrecognized vehicle $\rightarrow$ Trigger `RULE_REPEAT_VEHICLE_ENTRY` alert.
