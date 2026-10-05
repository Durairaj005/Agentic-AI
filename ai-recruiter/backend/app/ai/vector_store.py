import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from app.ai.embeddings import embedding_service
from app.models.candidate import Candidate

logger = logging.getLogger(__name__)

INDEX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "faiss_indexes"))
INDEX_FILE = os.path.join(INDEX_DIR, "candidates.index")
META_FILE = os.path.join(INDEX_DIR, "candidates_meta.json")
VECTOR_DIM = 384


class VectorStore:
    def __init__(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
        self.dimension = VECTOR_DIM
        self.index = None
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Load persisted index and metadata from disk, or initialize fresh IndexFlatIP."""
        if FAISS_AVAILABLE:
            if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
                try:
                    self.index = faiss.read_index(INDEX_FILE)
                    with open(META_FILE, "r", encoding="utf-8") as f:
                        # JSON keys are strings, convert back to int
                        raw_meta = json.load(f)
                        self.metadata = {int(k): v for k, v in raw_meta.items()}
                    logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                    return
                except Exception as e:
                    logger.warning(f"Could not load existing FAISS index: {e}. Reinitializing.")

            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = {}
        else:
            logger.warning("FAISS is not installed. Using in-memory numpy fallback.")
            self.index = None
            self.metadata = {}

    def _save(self):
        """Persist FAISS index and metadata map to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return
        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(META_FILE, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist FAISS index: {e}")

    def add_candidate(
        self,
        candidate_id: str,
        name: str,
        text: str,
        skills: List[str],
        experience: float,
        location: str,
        email: str
    ):
        """Embed and index candidate dossier."""
        vector = embedding_service.get_embedding(text)
        vector_np = np.array([vector], dtype=np.float32)

        # Normalize vector for cosine similarity via inner product
        norm = np.linalg.norm(vector_np)
        if norm > 0:
            vector_np = vector_np / norm

        if FAISS_AVAILABLE and self.index is not None:
            doc_id = self.index.ntotal
            self.index.add(vector_np)
            self.metadata[doc_id] = {
                "candidate_id": candidate_id,
                "name": name,
                "skills": skills,
                "experience": experience,
                "location": location,
                "email": email,
                "summary": text[:250]
            }
            self._save()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search against candidate index using query embedding."""
        if not query or not query.strip():
            return []

        query_vec = embedding_service.get_embedding(query)
        query_np = np.array([query_vec], dtype=np.float32)
        norm = np.linalg.norm(query_np)
        if norm > 0:
            query_np = query_np / norm

        results: List[Dict[str, Any]] = []

        if FAISS_AVAILABLE and self.index is not None and self.index.ntotal > 0:
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_np, k)

            for score, idx in zip(distances[0], indices[0]):
                if idx in self.metadata and idx != -1:
                    item = dict(self.metadata[idx])
                    # Inner product on normalized vectors is in range [-1.0, 1.0], convert to 0-100%
                    sim_pct = round(float(max(0.0, (score + 1.0) / 2.0)) * 100, 1)
                    item["similarity_score"] = sim_pct
                    item["raw_cosine"] = round(float(score), 4)
                    results.append(item)

        return results

    def rebuild_index(self, db: Session) -> Dict[str, Any]:
        """Re-index all candidates in the database."""
        candidates = db.query(Candidate).all()
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = {}

        count = 0
        for cand in candidates:
            # Construct rich semantic representation
            skill_tokens = [s.skill for s in cand.skills]
            doc_text = f"Candidate: {cand.name}. Experience: {cand.total_experience} years. Location: {cand.location}. Skills: {', '.join(skill_tokens)}. Summary: {cand.summary or ''} {cand.resume_raw_text or ''}"
            self.add_candidate(
                candidate_id=cand.id,
                name=cand.name,
                text=doc_text,
                skills=skill_tokens,
                experience=cand.total_experience,
                location=cand.location,
                email=cand.email
            )
            count += 1

        self._save()
        return {
            "message": f"Successfully indexed {count} candidates into FAISS vector index.",
            "total_vectors": count,
            "dimension": self.dimension
        }


vector_store = VectorStore()
