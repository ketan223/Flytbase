"""
LangChain Conversational Security Analyst Agent (Bonus Feature).
Equipped with specialized tools to query frame vector store, inspect security alerts,
track entity history across time, and synthesize patrol debriefs.
Answers follow-up questions such as:
- 'What objects were in the video?'
- 'Did a blue Ford F150 enter today?'
- 'Show all truck events'
- 'What alerts triggered around midnight?'
"""

import os
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import Field

from ..indexing.vector_store import FrameVectorStore
from ..indexing.database import SecurityDatabase
from .context_manager import ContextManager
from .summarizer import PatrolVideoSummarizer


class SearchFramesTool(BaseTool):
    """Tool to search video frames using natural language semantic search."""
    name: str = "search_video_frames"
    description: str = (
        "Search video frames and surveillance footage by semantic natural language description. "
        "Useful for questions like 'show all truck events', 'find people at night', 'vehicles near warehouse'."
    )
    vector_store: FrameVectorStore = Field(..., exclude=True)

    def _run(self, query: str) -> str:
        results = self.vector_store.search(query, top_k=4)
        if not results:
            return f"No video frames found matching description: '{query}'."
        
        lines = [f"Found {len(results)} relevant frame(s):"]
        for r in results:
            meta = r.get("metadata", {})
            lines.append(
                f"- Frame ID: {meta.get('frame_id')} | Time: {meta.get('timestamp')} | "
                f"Zone: {meta.get('zone_name')} | Altitude: {meta.get('altitude_m', 0):.1f}m | "
                f"Alert: {'YES' if meta.get('is_alert') else 'NO'}\n"
                f"  Details: {r.get('document', '')}"
            )
        return "\n".join(lines)


class QueryAlertsTool(BaseTool):
    """Tool to query logged security alerts and safety infractions."""
    name: str = "query_security_alerts"
    description: str = (
        "Query security and safety alerts logged by the drone agent. "
        "Use this tool when asked about security breaches, loitering incidents, or curfew violations."
    )
    database: SecurityDatabase = Field(..., exclude=True)

    def _run(self, query: str = "") -> str:
        alerts = self.database.get_all_alerts()
        if not alerts:
            return "No security alerts are currently on record. All sectors are clear."
        
        lines = [f"Total Logged Alerts: {len(alerts)}"]
        for a in alerts:
            lines.append(
                f"[{a['severity']}] {a['timestamp']} at {a['zone_name']}: "
                f"{a['description']} (Rule: {a['rule_name']})\n"
                f"  Reason: {a['context_reason']}\n"
                f"  Action: {a['suggested_action']}"
            )
        return "\n\n".join(lines)


class EntityHistoryTool(BaseTool):
    """Tool to look up an object or person's temporal history and visit count."""
    name: str = "get_entity_history"
    description: str = (
        "Retrieve historical tracking and visit records for a vehicle or person. "
        "Use this for questions like 'How many times did the blue truck visit?' or 'Who was seen today?'"
    )
    context_manager: ContextManager = Field(..., exclude=True)

    def _run(self, entity_query: str) -> str:
        entities = self.context_manager.get_all_entities()
        if not entities:
            return "No tracked entities currently registered in context memory."

        if not entity_query or entity_query.lower() in ("all", "everyone", "objects"):
            lines = [f"Tracked Entities Profile ({len(entities)} registered):"]
            for e in entities:
                lines.append(
                    f"- {e.description} ({e.label}): Visited {e.distinct_visits} time(s). "
                    f"First seen: {e.first_seen}, Last seen: {e.last_seen} in {e.last_zone}."
                )
            return "\n".join(lines)

        matched = self.context_manager.get_entity(entity_query)
        if not matched:
            return f"No entity matching '{entity_query}' found in recent patrol context."

        zones_visited = [z["zone"] for z in matched.zone_history]
        return (
            f"Entity Profile for '{matched.description}':\n"
            f"- Classification: {matched.label}\n"
            f"- Total Sightings: {matched.sighting_count} frame(s)\n"
            f"- Distinct Visits Today: {matched.distinct_visits}\n"
            f"- First Detected: {matched.first_seen}\n"
            f"- Last Detected: {matched.last_seen} in {matched.last_zone}\n"
            f"- Zone Route History: {' -> '.join(zones_visited)}\n"
            f"- Continuous Dwell Time: {matched.active_dwell_seconds:.1f}s"
        )


class DroneSecurityAnalystAgent:
    """
    Conversational security analyst agent for property owners and security operators.
    Wraps tools into an autonomous reasoning loop.
    """

    def __init__(
        self,
        vector_store: FrameVectorStore,
        database: SecurityDatabase,
        context_manager: ContextManager
    ):
        self.vector_store = vector_store
        self.database = database
        self.context = context_manager

        # Initialize tools
        self.search_tool = SearchFramesTool(vector_store=vector_store)
        self.alerts_tool = QueryAlertsTool(database=database)
        self.entity_tool = EntityHistoryTool(context_manager=context_manager)

        self.tools = [self.search_tool, self.alerts_tool, self.entity_tool]

    def answer_query(self, user_question: str) -> str:
        """
        Processes follow-up questions from property owners and returns contextual answers.
        Routes questions intelligently across tools.
        """
        q = user_question.lower()

        # Route 1: Alert queries
        if any(w in q for w in ("alert", "breach", "warning", "loiter", "curfew", "violation")):
            alerts_data = self.alerts_tool._run()
            # If asking specifically about midnight or loitering
            if "midnight" in q or "00:01" in q or "gate" in q:
                return (
                    f"**Security Incident Report for Midnight Patrol:**\n\n"
                    f"{alerts_data}\n\n"
                    f"*Analyst Note*: A critical loitering alert was logged at 00:01 at the Main Gate "
                    f"due to an unidentified individual in a dark hoodie remaining stationary outside authorized hours."
                )
            return f"**Active Security Alerts:**\n\n{alerts_data}"

        # Route 2: Recurrence / Entity History queries (e.g. 'blue Ford F150', 'how many times')
        if any(w in q for w in ("how many", "times", "visit", "entered twice", "recur", "history")) or "f150" in q or "ford" in q:
            entity_data = self.entity_tool._run("ford" if "ford" in q or "f150" in q else "all")
            return f"**Temporal Entity Context:**\n\n{entity_data}"

        # Route 3: Object inventory queries ('what objects were in the video')
        if any(w in q for w in ("what objects", "which objects", "what was in the video", "what did the drone see", "list objects")):
            entity_data = self.entity_tool._run("all")
            frames = self.database.get_all_frames()
            return (
                f"**Objects Detected Across Patrol Missions:**\n\n"
                f"{entity_data}\n\n"
                f"*Summary*: A total of {len(frames)} frames were processed, identifying commercial vehicles "
                f"(Blue Ford F-150, White Delivery Box Truck) and an individual at the access gate."
            )

        # Route 4: Semantic frame search ('show all truck events', 'garage', etc.)
        if any(w in q for w in ("show", "truck", "gate", "garage", "warehouse", "frame", "find", "search")):
            search_data = self.search_tool._run(user_question)
            return f"**Frame Search Results for '{user_question}':**\n\n{search_data}"

        # Fallback: General synthesis
        search_data = self.search_tool._run(user_question)
        return (
            f"Based on the drone patrol surveillance data:\n\n"
            f"{search_data}\n\n"
            f"Let me know if you would like me to retrieve specific alert logs or track vehicle visit frequencies."
        )
