"""
Master Pipeline Orchestrator for Drone Security Analyst Agent.
Coordinates telemetry ingestion, VLM visual inference, context management,
security rule evaluation, dual database indexing (SQLite + ChromaDB), and video summarization.
"""

import os
from typing import List, Dict, Any, Optional
from .telemetry.drone_simulator import DroneMissionSimulator
from .telemetry.models import FrameAnalysis, SecurityAlert, PatrolSummary
from .vision.vlm_analyzer import VLMAnalyzer
from .vision.annotator import FrameAnnotator
from .agent.context_manager import ContextManager
from .agent.security_rules import SecurityRuleEngine
from .agent.summarizer import PatrolVideoSummarizer
from .agent.langchain_agent import DroneSecurityAnalystAgent
from .indexing.database import SecurityDatabase
from .indexing.vector_store import FrameVectorStore


class DroneSecurityPipeline:
    """End-to-end security pipeline for docked autonomous surveillance drones."""

    def __init__(
        self,
        db_path: str = "data/drone_security.db",
        vector_db_path: str = "data/chroma_db",
        flight_log_path: str = "data/sample_flight_logs.json"
    ):
        self.simulator = DroneMissionSimulator(flight_log_path=flight_log_path)
        self.vlm = VLMAnalyzer()
        self.context = ContextManager()
        self.rules = SecurityRuleEngine(context_manager=self.context)
        self.db = SecurityDatabase(db_path=db_path)
        self.vector_store = FrameVectorStore(persist_dir=vector_db_path)
        self.agent = DroneSecurityAnalystAgent(
            vector_store=self.vector_store,
            database=self.db,
            context_manager=self.context
        )

        self.processed_frames: List[FrameAnalysis] = []
        self.triggered_alerts: List[SecurityAlert] = []
        self.generated_logs: List[str] = []

    def run_all_patrols(self) -> Dict[str, Any]:
        """Process all simulated surveillance missions sequentially."""
        missions = self.simulator.get_all_missions()
        results = {}
        for m_id in missions:
            results[m_id] = self.run_mission(m_id)
        return results

    def run_mission(self, mission_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an autonomous surveillance patrol flight.
        Ingests frames, derives visual context, detects security breaches, and indexes results.
        """
        mission_frames: List[FrameAnalysis] = []
        mission_alerts: List[SecurityAlert] = []
        annotated_dir = "data/annotated_frames"
        os.makedirs(annotated_dir, exist_ok=True)

        for frame in self.simulator.stream_mission(mission_id=mission_id):
            # 1. Update temporal context & recurrence tracking
            logs = self.context.process_frame(frame)
            self.generated_logs.extend(logs)

            # 2. Evaluate security policies & rules
            alerts = self.rules.evaluate_frame(frame)
            for alert in alerts:
                self.db.insert_alert(alert)
                mission_alerts.append(alert)
                self.triggered_alerts.append(alert)

            # 3. Annotate tactical frame visual overlay
            ann_path = os.path.join(annotated_dir, f"annotated_{frame.frame_id}.png")
            FrameAnnotator.annotate(
                frame,
                alert=alerts[0] if alerts else None,
                save_path=ann_path
            )

            # 4. Relational & Vector Indexing
            self.db.insert_frame(frame)
            self.vector_store.index_frame(frame)

            mission_frames.append(frame)
            self.processed_frames.append(frame)

        # 5. Generate automated video patrol summary
        m_id = mission_id or (mission_frames[0].mission_id if mission_frames else "PATROL_UNKNOWN")
        summary = PatrolVideoSummarizer.generate_summary(m_id, mission_frames, mission_alerts)

        return {
            "mission_id": m_id,
            "frames": mission_frames,
            "alerts": mission_alerts,
            "logs": self.generated_logs,
            "summary": summary
        }
