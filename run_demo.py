"""
FlytBase Drone Security Analyst Agent — Quick CLI Demonstration.
Runs both Day and Night autonomous patrol flights, outputs logs and alerts,
tests semantic frame indexing, and demonstrates LangChain Q&A.
"""

import sys
import os

# Ensure UTF-8 output encoding across Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.pipeline import DroneSecurityPipeline


def main():
    print("=" * 75)
    print("   [FLYTBASE] AUTONOMOUS DRONE SECURITY ANALYST AGENT DEMO   ")
    print("=" * 75)

    pipeline = DroneSecurityPipeline()
    print("\n[+] Initializing Autonomous Drone-in-a-Box Security Pipeline...")
    print(f"    - Database (SQLite): {pipeline.db.db_path}")
    print(f"    - Vector Store (ChromaDB): {pipeline.vector_store.persist_dir}")
    print("    - VLM & Rules Engine: Active")

    print("\n[1] EXECUTING AUTONOMOUS PATROL MISSIONS...")
    results = pipeline.run_all_patrols()

    for m_id, res in results.items():
        print(f"\n--- MISSION DEBRIEF: {m_id} ---")
        summary = res["summary"]
        print(f"* Summary: {summary.one_sentence_summary}")
        print(f"* Frames Processed: {len(res['frames'])}")
        print(f"* Alerts Triggered: {len(res['alerts'])}")
        for a in res["alerts"]:
            print(f"  [ALERT - {a.severity.value}] {a.timestamp} ({a.zone_name}): {a.description}")

    print("\n" + "=" * 75)
    print("[2] TESTING GENERATED OPERATIONAL LOGS:")
    for log in pipeline.generated_logs[:5]:
        print(f"  [LOG] {log}")

    print("\n" + "=" * 75)
    print("[3] TESTING CROSS-DOMAIN SEMANTIC FRAME SEARCH:")
    query = "show all truck events"
    print(f"  [SEARCH] Query: '{query}'")
    search_results = pipeline.vector_store.search(query, top_k=3)
    for r in search_results:
        meta = r.get("metadata", {})
        print(f"    -> [{meta.get('frame_id')}] Time: {meta.get('timestamp')} | Zone: {meta.get('zone_name')} | Score: {r.get('score', 0):.2f}")
        print(f"       Details: {r.get('document', '')[:100]}...")

    print("\n" + "=" * 75)
    print("[4] TESTING LANGCHAIN SECURITY ANALYST AGENT (BONUS Q&A):")
    questions = [
        "What objects were in the video?",
        "Did the blue Ford F150 enter twice today?",
        "What alerts triggered at midnight?"
    ]
    for q in questions:
        print(f"\n[?] User Question: {q}")
        answer = pipeline.agent.answer_query(q)
        print(f"[!] Agent Answer:\n{answer}")

    print("\n" + "=" * 75)
    print("[OK] DEMO EXECUTION COMPLETE!")
    print("To launch the full interactive web dashboard, run:")
    print("   streamlit run dashboard/app.py")
    print("=" * 75)


if __name__ == "__main__":
    main()
