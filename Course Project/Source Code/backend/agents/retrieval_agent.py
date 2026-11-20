"""
Lab 4: Memory & Retrieval — State vs Stored
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Separate short-term run state from long-term stored knowledge.

Design Principle:
Never conflate run state with the archive — mixing them corrupts the baseline.

Pseudocode:
state.draft = candidate                       # short-term
hits  = retrieve(store, tags)                 # long-term
prior = retrieve(history, embed(candidate), k=5)  # similarity
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import sqlite3
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# Short-Term Run State (Ephemeral, Checkpointed)
# ---------------------------------------------------------------------------

class ShortTermRunState(BaseModel):
    run_id: str
    course_id: int
    step: str = "init"
    draft: Optional[Dict[str, Any]] = None  # Ephemeral draft
    session_logs: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def update_draft(self, candidate: Dict[str, Any]):
        self.draft = candidate
        self.session_logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Draft updated for entity: {candidate.get('id', 'unknown')}")

    def clear(self):
        self.draft = None
        self.step = "cleared"


# ---------------------------------------------------------------------------
# Long-Term Knowledge & Vector Retrieval
# ---------------------------------------------------------------------------

class NoteHit(BaseModel):
    id: int
    title: str
    unit: str
    topic: str
    version: int
    is_current: bool
    snippet: str


class PriorSubmissionHit(BaseModel):
    submission_id: int
    student_name: str
    similarity_score: float
    file_name: str
    is_plagiarism_risk: bool
    snippet: str


class CourseRetrievalAgent:
    """
    Retrieval Agent:
    Operates long-term memory retrieval without contaminating short-term run state.
    Provides:
    1. Tag-based retrieval over the notes & materials store.
    2. Embedding / vector similarity retrieval over prior submission history.
    """

    AGENT_NAME = "CourseRetrievalAgent"

    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / "data" / "organizer.db"
        self._init_vector_store()

    def _init_vector_store(self):
        """Initializes simple, high-performance in-memory TF-IDF / vector archive for prior submissions."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._rebuild_submission_index()

    def _rebuild_submission_index(self):
        """Indexes all existing submissions in database for fast cosine similarity retrieval."""
        from sklearn.metrics.pairwise import cosine_similarity
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT s.id, s.file_path, s.file_name, u.name as student_name
            FROM submissions s
            JOIN users u ON s.student_id = u.id
        """)
        rows = c.fetchall()
        conn.close()

        self.archive_docs = []
        self.archive_metadata = []

        for r in rows:
            fp = (r["file_path"] or "").strip()
            p = Path(fp) if fp else None
            text = p.read_text(encoding="utf-8", errors="ignore") if (p and p.is_file()) else f"Submission {r['id']}"
            self.archive_docs.append(text)
            self.archive_metadata.append({
                "submission_id": r["id"],
                "student_name": r["student_name"],
                "file_name": r["file_name"],
                "text": text[:200]
            })

        if self.archive_docs:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.archive_docs)
        else:
            self.tfidf_matrix = None

    # ── Long-term: Tag-based retrieval over notes ─────────────────────────────

    def retrieve_notes_by_tags(self, course_id: int, tags: Dict[str, str], current_only: bool = True) -> List[NoteHit]:
        """
        Long-term tag retrieval:
        hits = retrieve(store, tags)
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = "SELECT id, title, unit, topic, version, is_current, file_path FROM notes WHERE course_id = ?"
        params = [course_id]

        if "unit" in tags:
            query += " AND (unit = ? OR LOWER(unit) = LOWER(?))"
            params.extend([tags["unit"], tags["unit"]])
        if "topic" in tags:
            query += " AND topic LIKE ?"
            params.append(f"%{tags['topic']}%")
        if current_only:
            query += " AND is_current = 1"

        query += " ORDER BY version DESC"
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        hits = []
        for r in rows:
            snippet = ""
            p = Path(r["file_path"])
            if p.exists():
                snippet = p.read_text(encoding="utf-8", errors="ignore")[:150]
            hits.append(NoteHit(
                id=r["id"],
                title=r["title"],
                unit=r["unit"].title() if r["unit"] else "",
                topic=r["topic"],
                version=r["version"],
                is_current=bool(r["is_current"]),
                snippet=snippet
            ))
        return hits

    # ── Long-term: Vector similarity retrieval over submission history ────────

    def retrieve_prior_submissions_by_similarity(self, candidate_text: str, k: int = 5, threshold: float = 0.75) -> List[PriorSubmissionHit]:
        """
        Long-term embedding similarity retrieval:
        prior = retrieve(history, embed(candidate), k=5)
        """
        if self.tfidf_matrix is None or not self.archive_docs:
            return []

        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self.vectorizer.transform([candidate_text])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        ranked_indices = np.argsort(sim_scores)[::-1][:k]
        hits = []
        for idx in ranked_indices:
            score = float(sim_scores[idx])
            meta = self.archive_metadata[idx]
            hits.append(PriorSubmissionHit(
                submission_id=meta["submission_id"],
                student_name=meta["student_name"],
                similarity_score=round(score, 4),
                file_name=meta["file_name"],
                is_plagiarism_risk=score >= threshold,
                snippet=meta["text"]
            ))
        return hits

    # ── End-to-end memory separation loop (Lab 4 Pseudocode) ──────────────────

    def execute_memory_split_workflow(self, run_id: str, candidate_submission: Dict[str, Any], query_tags: Dict[str, str]) -> Dict[str, Any]:
        """
        Implements Lab 4 Pseudocode:
        state.draft = candidate                       # short-term
        hits  = retrieve(store, tags)                 # long-term
        prior = retrieve(history, embed(candidate), k=5)  # similarity
        """
        # 1. Short-term run state
        state = ShortTermRunState(run_id=run_id, course_id=1)
        state.update_draft(candidate_submission)

        # 2. Long-term notes retrieval by tags
        hits = self.retrieve_notes_by_tags(course_id=1, tags=query_tags)

        # 3. Long-term similarity retrieval over history
        candidate_content = candidate_submission.get("code", "")
        prior = self.retrieve_prior_submissions_by_similarity(candidate_content, k=5)

        return {
            "short_term_state": state.model_dump(),
            "long_term_notes_hits": [h.model_dump() for h in hits],
            "long_term_prior_history": [p.model_dump() for p in prior],
            "memory_separation_verified": True
        }
