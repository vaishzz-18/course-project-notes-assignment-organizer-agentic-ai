"""
Plagiarism/Similarity Agent — checks submissions for similarity and flags high-similarity cases.
Uses TF-IDF + cosine similarity for fast batch checks.

Plagiarism Policy (timestamp-based):
  - If two or more submissions share > SIMILARITY_THRESHOLD similarity:
    * The student who submitted FIRST (earliest submitted_at) is considered ORIGINAL.
    * All students who submitted AFTER the first are marked PLAGIARISED and assigned 0 marks.
  - Faculty is notified of all flags for final review. The agent never finalises grades independently.
"""
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Submission, Grade, GradeStatus
from runtime.audit import AuditLogger
from config import settings


def _extract_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            import fitz
            doc = fitz.open(str(path))
            return " ".join(page.get_text() for page in doc)
        elif suffix in (".docx", ".doc"):
            from docx import Document
            doc = Document(str(path))
            return " ".join(p.text for p in doc.paragraphs)
        else:
            return path.read_text(errors="ignore")
    except Exception:
        return ""


def _cosine_similarity(texts: List[str]) -> List[List[float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    import numpy as np

    if len(texts) < 2:
        return [[1.0]] if texts else []

    vec = TfidfVectorizer(stop_words="english", min_df=1)
    try:
        tfidf = vec.fit_transform(texts)
        matrix = sk_cosine(tfidf).tolist()
        return matrix
    except Exception:
        return [[0.0] * len(texts) for _ in texts]


class PlagiarismSimilarityAgent:
    AGENT_NAME = "PlagiarismSimilarityAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def step(self, submissions: List[Submission]):
        """Pipeline step: run similarity for a batch of submissions, then apply timestamp-based plagiarism policy."""
        if len(submissions) < 2:
            if submissions:
                submissions[0].similarity_score = 0.0
                submissions[0].similarity_flags = json.dumps([])
                await self.db.flush()
            return

        texts = [_extract_text(s.file_path) for s in submissions]
        matrix = _cosine_similarity(texts)

        # Build a lookup of submission id -> index for quick access
        idx_map = {s.id: i for i, s in enumerate(submissions)}

        # Step 1: Assign similarity scores and flags per submission
        for i, sub in enumerate(submissions):
            scores = [matrix[i][j] for j in range(len(submissions)) if j != i]
            max_score = max(scores) if scores else 0.0
            flags = []
            for j, other in enumerate(submissions):
                if j != i and matrix[i][j] > settings.SIMILARITY_THRESHOLD:
                    flags.append({
                        "with_submission_id": other.id,
                        "with_student_id": other.student_id,
                        "score": round(matrix[i][j], 3),
                        "flagged": True,
                    })
            sub.similarity_score = round(max_score, 3)
            sub.similarity_flags = json.dumps(flags)

        await self.db.flush()

        # Step 2: Apply timestamp-based plagiarism rule for clusters of flagged submissions
        # Find all pairs above threshold and group them into plagiarism clusters
        threshold = settings.SIMILARITY_THRESHOLD
        plagiarism_clusters: List[set] = []

        for i in range(len(submissions)):
            for j in range(i + 1, len(submissions)):
                if matrix[i][j] > threshold:
                    si = submissions[i]
                    sj = submissions[j]
                    # Find or create a cluster containing both
                    merged = False
                    for cluster in plagiarism_clusters:
                        if si.id in cluster or sj.id in cluster:
                            cluster.add(si.id)
                            cluster.add(sj.id)
                            merged = True
                            break
                    if not merged:
                        plagiarism_clusters.append({si.id, sj.id})

        # Merge overlapping clusters (union-find style)
        merged = True
        while merged:
            merged = False
            for a in range(len(plagiarism_clusters)):
                for b in range(a + 1, len(plagiarism_clusters)):
                    if plagiarism_clusters[a] & plagiarism_clusters[b]:
                        plagiarism_clusters[a] = plagiarism_clusters[a] | plagiarism_clusters[b]
                        plagiarism_clusters.pop(b)
                        merged = True
                        break
                if merged:
                    break

        # Step 3: For each cluster, the EARLIEST submitter is original; all others get 0 marks
        sub_map = {s.id: s for s in submissions}
        plagiarised_submission_ids = set()
        original_submission_ids = set()
        original_by_sub_id = {}

        for cluster in plagiarism_clusters:
            cluster_subs = [sub_map[sid] for sid in cluster if sid in sub_map]
            # Sort by submitted_at ascending — first is original
            cluster_subs_sorted = sorted(cluster_subs, key=lambda s: s.submitted_at)
            original = cluster_subs_sorted[0]
            plagiarists = cluster_subs_sorted[1:]

            original_submission_ids.add(original.id)
            # Tag original submission flags
            original.similarity_flags = json.dumps([{
                "role": "original",
                "status": "original_submission",
                "score": original.similarity_score,
                "note": "First to submit in similarity cluster — verified as original work.",
                "cluster_size": len(cluster_subs),
                "submitted_at": original.submitted_at.isoformat() if original.submitted_at else "",
            }])

            for ps in plagiarists:
                plagiarised_submission_ids.add(ps.id)
                original_by_sub_id[ps.id] = original
                ps.similarity_flags = json.dumps([{
                    "role": "plagiarised",
                    "status": "plagiarism_penalty",
                    "with_submission_id": original.id,
                    "with_student_id": original.student_id,
                    "score": ps.similarity_score,
                    "note": f"Submitted after original submission (Student #{original.student_id}). Awarded 0 marks.",
                    "submitted_at": ps.submitted_at.isoformat() if ps.submitted_at else "",
                }])

        # Step 4: Apply 0-mark penalty to plagiarised submissions via the Grade table
        if plagiarised_submission_ids:
            for sub_id in plagiarised_submission_ids:
                orig = original_by_sub_id.get(sub_id)
                orig_student_ref = f"Student #{orig.student_id}" if orig else "an earlier peer"
                grade_res = await self.db.execute(
                    select(Grade).where(Grade.submission_id == sub_id)
                )
                existing_grade = grade_res.scalar_one_or_none()

                plagiarism_feedback = (
                    f"⚠ Plagiarism Policy Applied: This submission shares >{int(settings.SIMILARITY_THRESHOLD * 100)}% "
                    f"similarity with an earlier submission ({orig_student_ref}). Per course policy, "
                    "only the first submission is recognized as original work. All later matching submissions "
                    "receive 0 marks."
                )
                evidence = json.dumps({
                    "policy": "timestamp_first_submitter_original",
                    "plagiarism_flagged": True,
                    "original_student_id": orig.student_id if orig else None,
                    "original_submission_id": orig.id if orig else None,
                    "similarity_score": sub_map[sub_id].similarity_score,
                })
                zero_rubric = json.dumps({
                    "academic_integrity": {"marks": 0.0, "max": 100, "comment": "Plagiarism detected: later submission matching earlier peer."}
                })

                if existing_grade:
                    existing_grade.draft_marks = 0.0
                    existing_grade.draft_feedback = plagiarism_feedback
                    existing_grade.draft_rubric_breakdown = zero_rubric
                    existing_grade.evidence_record = evidence
                    existing_grade.status = GradeStatus.pending_approval
                else:
                    new_grade = Grade(
                        submission_id=sub_id,
                        draft_marks=0.0,
                        draft_feedback=plagiarism_feedback,
                        draft_rubric_breakdown=zero_rubric,
                        evidence_record=evidence,
                        status=GradeStatus.pending_approval,
                    )
                    self.db.add(new_grade)

            await self.db.flush()

        flagged_count = len(plagiarism_clusters)
        plagiarist_count = len(plagiarised_submission_ids)

        await self.audit.log(
            self.AGENT_NAME, "similarity_batch_complete",
            input_data={"submission_count": len(submissions)},
            output_data={
                "flagged_clusters": flagged_count,
                "plagiarists_zeroed": plagiarist_count,
                "originals_protected": len(original_submission_ids),
                "threshold": settings.SIMILARITY_THRESHOLD,
                "policy": "first_submitter_original_later_submitters_zeroed",
            },
        )
