"""
Video Patrol Summarizer (Bonus Feature).
Generates concise 1-sentence summaries and executive security debriefs
from analyzed drone patrol video frames and telemetry.
"""

from typing import List, Dict
from ..telemetry.models import FrameAnalysis, SecurityAlert, PatrolSummary


class PatrolVideoSummarizer:
    """Aggregates multi-frame surveillance observations and generates automated mission summaries."""

    @staticmethod
    def generate_summary(
        mission_id: str,
        frames: List[FrameAnalysis],
        alerts: List[SecurityAlert]
    ) -> PatrolSummary:
        """Synthesize a complete mission summary and 1-sentence synopsis."""
        if not frames:
            return PatrolSummary(
                mission_id=mission_id,
                start_time="N/A",
                end_time="N/A",
                total_frames=0,
                total_alerts=0,
                alerts_by_severity={"INFO": 0, "WARNING": 0, "CRITICAL": 0},
                one_sentence_summary="No patrol frames were processed for this mission.",
                executive_summary="Empty mission flight record.",
                key_events=[],
                zones_covered=[]
            )

        start_time = frames[0].timestamp
        end_time = frames[-1].timestamp
        zones = sorted(list(set(f.telemetry.zone_name for f in frames)))

        # Count alerts by severity
        sev_counts = {"INFO": 0, "WARNING": 0, "CRITICAL": 0}
        for a in alerts:
            sev_counts[a.severity.value] = sev_counts.get(a.severity.value, 0) + 1

        # Identify unique objects detected
        objects_seen = set()
        for f in frames:
            for obj in f.detected_objects:
                objects_seen.add(obj.description)

        # 1-Sentence concise summary
        if alerts:
            top_alert = alerts[0].description
            one_sentence = (
                f"Patrol mission {mission_id} completed across {len(zones)} zones ({len(frames)} frames): "
                f"{len(alerts)} security alert(s) triggered, including {top_alert}"
            )
        else:
            one_sentence = (
                f"Patrol mission {mission_id} completed across {len(zones)} zones ({len(frames)} frames): "
                f"Perimeter secure, no unauthorized breaches or safety violations detected."
            )

        # Build chronological key events
        key_events = []
        for f in frames:
            if f.detected_objects:
                objs_str = ", ".join([o.description for o in f.detected_objects])
                key_events.append(f"[{f.timestamp}] {f.telemetry.zone_name}: {objs_str} ({f.activity_summary})")

        for a in alerts:
            key_events.append(f"[ALERT - {a.severity.value}] {a.timestamp} in {a.zone_name}: {a.description}")

        # Formulate executive briefing
        exec_briefing = (
            f"AUTONOMOUS DRONE PATROL DEBRIEF (Mission: {mission_id})\n"
            f"Operation Period: {start_time} to {end_time}\n"
            f"Coverage: {len(zones)} distinct property sectors inspected: {', '.join(zones)}.\n"
            f"Visual Feeds Ingested: {len(frames)} frames analyzed with real-time VLM inference.\n"
            f"Entities Identified: {', '.join(objects_seen) if objects_seen else 'None'}.\n"
            f"Alert Incident Count: {len(alerts)} total ({sev_counts.get('CRITICAL', 0)} Critical, {sev_counts.get('WARNING', 0)} Warning).\n"
            f"Primary Disposition: {'Security follow-up required due to rule breaches.' if alerts else 'All inspected sectors confirmed secure.'}"
        )

        return PatrolSummary(
            mission_id=mission_id,
            start_time=start_time,
            end_time=end_time,
            total_frames=len(frames),
            total_alerts=len(alerts),
            alerts_by_severity=sev_counts,
            one_sentence_summary=one_sentence,
            executive_summary=exec_briefing,
            key_events=key_events,
            zones_covered=zones
        )
