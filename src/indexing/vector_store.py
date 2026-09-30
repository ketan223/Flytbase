"""
Vector Store for Frame-by-Frame Cross-Domain Indexing and Natural Language Search.
Uses ChromaDB and semantic embeddings to allow natural language queries over video frames
(e.g., 'show all truck events', 'person loitering at midnight', 'delivery vehicles').
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from ..telemetry.models import FrameAnalysis


class FrameVectorStore:
    """
    Semantic frame indexer enabling natural language search over drone surveillance footage.
    """

    def __init__(self, persist_dir: str = "data/chroma_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="drone_surveillance_frames",
            metadata={"description": "Indexed aerial surveillance frames with captions and telemetry"}
        )

    def index_frame(self, frame: FrameAnalysis):
        """Index a single frame's visual caption, telemetry, and entity context."""
        objects_str = ", ".join([f"{o.label} ({o.description})" for o in frame.detected_objects])
        document_text = (
            f"Frame {frame.frame_id} captured at {frame.timestamp}. "
            f"Zone: {frame.telemetry.zone_name}. Altitude: {frame.telemetry.altitude_m:.1f}m. "
            f"Caption: {frame.caption}. "
            f"Detected Objects: {objects_str if objects_str else 'none'}. "
            f"Activity: {frame.activity_summary}"
        )

        metadata = {
            "frame_id": frame.frame_id,
            "mission_id": frame.mission_id,
            "timestamp": frame.timestamp,
            "zone_name": frame.telemetry.zone_name,
            "altitude_m": float(frame.telemetry.altitude_m),
            "image_path": frame.image_path,
            "is_alert": 1 if frame.is_alert else 0,
            "object_count": len(frame.detected_objects),
            "has_vehicle": 1 if any(o.label == "vehicle" for o in frame.detected_objects) else 0,
            "has_person": 1 if any(o.label == "person" for o in frame.detected_objects) else 0,
        }

        self.collection.upsert(
            ids=[frame.frame_id],
            documents=[document_text],
            metadatas=[metadata]
        )

    def search(self, query: str, top_k: int = 4, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute semantic natural language search across all indexed video frames.
        Returns top matching frames with distance scores and metadata.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where
        )

        output = []
        if results and "ids" in results and results["ids"]:
            ids = results["ids"][0]
            docs = results["documents"][0] if "documents" in results else []
            metas = results["metadatas"][0] if "metadatas" in results else []
            distances = results["distances"][0] if "distances" in results else []

            for i in range(len(ids)):
                output.append({
                    "frame_id": ids[i],
                    "document": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "score": float(1.0 - distances[i]) if i < len(distances) and distances[i] is not None else 1.0
                })

        return output

    def count(self) -> int:
        """Return total indexed frames."""
        return self.collection.count()
