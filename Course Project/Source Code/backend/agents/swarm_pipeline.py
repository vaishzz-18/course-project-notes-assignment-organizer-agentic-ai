"""
Lab 8: Parallel Swarm — Fan-Out / Fan-In Processing
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Replace the sequential similarity + grading loop from Lab 7 with an asynchronous
worker pool that processes ALL submissions concurrently (fan-out), then merges
them into a plan-aligned workspace draft (fan-in).

Pseudocode:
  workers = [Worker(sub) for sub in submissions]
  results = await asyncio.gather(*workers)       # fan-out
  draft   = merge(results, plan)                 # fan-in

Acceptance Criteria:
  • Each submission is graded by its own independent async worker.
  • Wall-clock time for parallel execution is measurably faster than sequential.
  • The merged draft is plan-aligned (every assignment in plan has a results section).
  • Similarity cross-check is also parallelised across submission pairs.
  • Results are governed by AURAControlledRuntime (audit-logged).
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from runtime.governed_runtime import AURAControlledRuntime, RuntimeBudget

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent.parent.parent / "data" / "organizer.db"


def _query(sql: str, params: tuple = ()) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


class SubmissionPayload(BaseModel):
    """Input payload for a single swarm worker."""
    submission_id: int
    student_name: str
    student_id: int
    assignment_id: int
    assignment_title: str
    file_name: str
    file_path: str
    submitted_at: str
    is_late: bool
    content: str


class WorkerResult(BaseModel):
    """Output from a single swarm worker (similarity + grading)."""
    submission_id: int
    student_name: str
    assignment_id: int
    assignment_title: str

    # Similarity
    similarity_scores: List[Dict[str, Any]]   # pairs vs other submissions
    is_plagiarism_risk: bool
    max_similarity: float

    # Grading
    rubric_breakdown: Dict[str, Any]
    raw_total: float
    deductions: List[Dict[str, Any]]
    final_marks: float
    plagiarism_held: bool

    # Worker metadata
    worker_id: str
    processed_at: str
    wall_time_ms: float


class SwarmMergedDraft(BaseModel):
    """Final plan-aligned merged workspace draft."""
    run_id: str
    course_id: int
    plan_aligned: bool
    total_submissions: int
    total_workers: int
    parallel_wall_time_ms: float
    sequential_estimate_ms: float
    speedup_factor: float

    # Per-assignment summaries
    assignment_summaries: List[Dict[str, Any]]

    # Raw worker results
    worker_results: List[Dict[str, Any]]
    similarity_flags: List[Dict[str, Any]]
    governance_audit_entries: int
    assembled_at: str


# ---------------------------------------------------------------------------
# Rubric Configuration
# ---------------------------------------------------------------------------

RUBRIC = {
    "understanding":  {"max": 25, "base_awarded": 20},
    "implementation": {"max": 40, "base_awarded": 35},
    "testing":        {"max": 20, "base_awarded": 16},
    "report":         {"max": 15, "base_awarded": 12},
}
LATE_PENALTY_PERCENT = 100
PLAGIARISM_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Individual Swarm Worker
# ---------------------------------------------------------------------------

async def swarm_worker(
    submission: SubmissionPayload,
    all_submissions: List[SubmissionPayload],
    worker_index: int,
) -> WorkerResult:
    """
    Async worker: independently processes one submission.
    Performs:
    1. Pairwise similarity against all OTHER submissions.
    2. Rubric-based grading with late penalty.
    3. Plagiarism hold if similarity exceeds threshold.
    """
    start_ms = time.perf_counter() * 1000
    worker_id = f"worker_{worker_index:02d}_{submission.submission_id}"

    # ── Step 1: Similarity scan ────────────────────────────────────────────
    similarity_scores: List[Dict[str, Any]] = []
    max_similarity = 0.0

    # Run CPU-bound TF-IDF in executor to avoid blocking the event loop
    loop = asyncio.get_running_loop()

    def compute_similarity() -> List[Dict[str, Any]]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as sk_cos

        others = [s for s in all_submissions if s.submission_id != submission.submission_id]
        if not others or not submission.content.strip():
            return []

        docs = [submission.content] + [o.content for o in others if o.content.strip()]
        if len(docs) < 2:
            return []

        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform(docs)
        sims = sk_cos(mat[0:1], mat[1:])[0]

        results = []
        for i, other in enumerate([o for o in others if o.content.strip()]):
            score = float(sims[i]) if i < len(sims) else 0.0
            results.append({
                "compared_to_id":   other.submission_id,
                "compared_to_name": other.student_name,
                "similarity_score": round(score, 4),
                "is_risk":          score >= PLAGIARISM_THRESHOLD,
            })
        return results

    similarity_scores = await loop.run_in_executor(None, compute_similarity)

    if similarity_scores:
        max_similarity = max(s["similarity_score"] for s in similarity_scores)
    is_plagiarism_risk = max_similarity >= PLAGIARISM_THRESHOLD

    # ── Step 2: Rubric grading ────────────────────────────────────────────
    raw_total = sum(v["base_awarded"] for v in RUBRIC.values())   # 83
    deductions: List[Dict[str, Any]] = []
    final = float(raw_total)

    if submission.is_late:
        penalty = final
        final = 0.0
        deductions.append({"reason": "late_submission", "deduction": penalty, "note": "Late submission policy: 0 marks awarded"})

    plagiarism_held = is_plagiarism_risk
    if plagiarism_held:
        deductions.append({"reason": "plagiarism_pending_review", "deduction": 0, "note": "Grade withheld"})
        final = 0.0

    rubric_breakdown = {
        k: {"max": v["max"], "awarded": v["base_awarded"]}
        for k, v in RUBRIC.items()
    }

    end_ms = time.perf_counter() * 1000
    wall_ms = round(end_ms - start_ms, 2)

    return WorkerResult(
        submission_id=submission.submission_id,
        student_name=submission.student_name,
        assignment_id=submission.assignment_id,
        assignment_title=submission.assignment_title,
        similarity_scores=similarity_scores,
        is_plagiarism_risk=is_plagiarism_risk,
        max_similarity=round(max_similarity, 4),
        rubric_breakdown=rubric_breakdown,
        raw_total=float(raw_total),
        deductions=deductions,
        final_marks=round(final, 1),
        plagiarism_held=plagiarism_held,
        worker_id=worker_id,
        processed_at=datetime.utcnow().isoformat(),
        wall_time_ms=wall_ms,
    )


# ---------------------------------------------------------------------------
# Sequential Baseline (for benchmarking)
# ---------------------------------------------------------------------------

async def run_sequential_baseline(submissions: List[SubmissionPayload]) -> float:
    """
    Runs workers one-by-one for timing comparison. Returns total wall-clock ms.
    """
    start = time.perf_counter()
    for i, sub in enumerate(submissions):
        await swarm_worker(sub, submissions, i)
    return round((time.perf_counter() - start) * 1000, 2)


# ---------------------------------------------------------------------------
# Swarm Coordinator
# ---------------------------------------------------------------------------

class SwarmCoordinator:
    """
    Orchestrates the parallel swarm:
    1. Loads all submissions for a course from the DB.
    2. Fan-out: launches one async worker per submission via asyncio.gather().
    3. Fan-in: merges all WorkerResults into a plan-aligned SwarmMergedDraft.
    4. Benchmarks parallel vs sequential wall-clock time.
    5. Audit-logs everything via AURAControlledRuntime.
    """

    def __init__(self, concurrency_limit: int = 10):
        self.concurrency_limit = concurrency_limit
        self.runtime = AURAControlledRuntime(
            budget=RuntimeBudget(max_steps=100, max_cost_tokens=500_000, timeout_seconds=180.0),
        )

    # ── Data Loading ─────────────────────────────────────────────────────────

    def _load_submissions(self, course_id: int) -> List[SubmissionPayload]:
        rows = _query(
            """
            SELECT s.id, s.file_name, s.file_path, s.submitted_at, s.is_late,
                   s.student_id, u.name as student_name,
                   a.id as assignment_id, a.title as assignment_title
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN assignments a ON s.assignment_id = a.id
            WHERE a.course_id = ?
            ORDER BY s.id
            """,
            (course_id,),
        )
        payloads = []
        for r in rows:
            file_path = Path(r["file_path"]) if r["file_path"] else None
            content = ""
            if file_path and file_path.exists():
                content = file_path.read_text(encoding="utf-8", errors="ignore")[:600]

            payloads.append(SubmissionPayload(
                submission_id=r["id"],
                student_name=r["student_name"],
                student_id=r["student_id"],
                assignment_id=r["assignment_id"],
                assignment_title=r["assignment_title"],
                file_name=r["file_name"],
                file_path=str(r["file_path"] or ""),
                submitted_at=r["submitted_at"],
                is_late=bool(r["is_late"]),
                content=content,
            ))
        return payloads

    def _load_plan(self, course_id: int) -> Dict[str, Any]:
        courses = _query("SELECT id, name, code FROM courses WHERE id = ?", (course_id,))
        assignments = _query(
            "SELECT id, title, due_date FROM assignments WHERE course_id = ?", (course_id,)
        )
        if not courses:
            return {}
        return {
            "course_name": courses[0]["name"],
            "course_code": courses[0]["code"],
            "assignments": [{"id": a["id"], "title": a["title"]} for a in assignments],
            "grading_policy": {
                "late_penalty_percent": LATE_PENALTY_PERCENT,
                "plagiarism_threshold": PLAGIARISM_THRESHOLD,
                "rubric_total_marks": 100,
            },
        }

    # ── Fan-In Merge ─────────────────────────────────────────────────────────

    def _merge_results(
        self,
        plan: Dict[str, Any],
        results: List[WorkerResult],
        run_id: str,
        parallel_ms: float,
        sequential_ms: float,
    ) -> SwarmMergedDraft:
        """
        Merges all worker results into a plan-aligned workspace draft.
        For each assignment in the plan, collects all submission results.
        """
        plan_assignments = plan.get("assignments", [])

        # Group results by assignment_id
        by_assignment: Dict[int, List[WorkerResult]] = {}
        for r in results:
            by_assignment.setdefault(r.assignment_id, []).append(r)

        # Build per-assignment summaries (plan-aligned)
        assignment_summaries = []
        for asgn in plan_assignments:
            asgn_id = asgn["id"]
            asgn_results = by_assignment.get(asgn_id, [])
            avg_marks = (
                round(sum(r.final_marks for r in asgn_results) / len(asgn_results), 1)
                if asgn_results else 0.0
            )
            assignment_summaries.append({
                "assignment_id":    asgn_id,
                "assignment_title": asgn.get("title", ""),
                "submission_count": len(asgn_results),
                "average_marks":    avg_marks,
                "withheld_count":   sum(1 for r in asgn_results if r.plagiarism_held),
                "late_count":       sum(1 for r in asgn_results if any(
                    d["reason"] == "late_submission" for d in r.deductions
                )),
                "marks_distribution": [
                    {"student": r.student_name, "final_marks": r.final_marks}
                    for r in asgn_results
                ],
            })

        # Collect all plagiarism flags (unique pairs, highest score)
        seen_pairs = set()
        similarity_flags: List[Dict[str, Any]] = []
        for r in results:
            for sim in r.similarity_scores:
                if sim["is_risk"]:
                    pair = tuple(sorted([r.submission_id, sim["compared_to_id"]]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        similarity_flags.append({
                            "submission_a_id":   r.submission_id,
                            "submission_b_id":   sim["compared_to_id"],
                            "student_a":         r.student_name,
                            "student_b":         sim["compared_to_name"],
                            "similarity_score":  sim["similarity_score"],
                            "is_plagiarism_risk": True,
                        })

        speedup = round(sequential_ms / parallel_ms, 2) if parallel_ms > 0 else 1.0
        plan_aligned = len(assignment_summaries) == len(plan_assignments)

        return SwarmMergedDraft(
            run_id=run_id,
            course_id=plan.get("course_id", 0),
            plan_aligned=plan_aligned,
            total_submissions=len(results),
            total_workers=len(results),
            parallel_wall_time_ms=round(parallel_ms, 2),
            sequential_estimate_ms=round(sequential_ms, 2),
            speedup_factor=speedup,
            assignment_summaries=assignment_summaries,
            worker_results=[r.model_dump() for r in results],
            similarity_flags=similarity_flags,
            governance_audit_entries=len(self.runtime.in_memory_audit),
            assembled_at=datetime.utcnow().isoformat(),
        )

    # ── Main Async Runner ─────────────────────────────────────────────────────

    async def run_async(
        self,
        course_id: int,
        faculty_id: int,
        run_id: Optional[str] = None,
    ) -> SwarmMergedDraft:
        """
        Full async swarm execution:
        1. Load submissions from DB.
        2. Run sequential baseline for benchmark.
        3. Fan-out: asyncio.gather all workers.
        4. Fan-in: merge into plan-aligned draft.
        5. Audit log + checkpoint.
        """
        run_id = run_id or f"lab8_{uuid.uuid4().hex[:10]}"

        # ── Load data ─────────────────────────────────────────────────────
        submissions = self._load_submissions(course_id)
        plan = self._load_plan(course_id)
        plan["course_id"] = course_id

        self.runtime.log_step(
            run_id, "SwarmCoordinator", "swarm_start",
            {"course_id": course_id, "submission_count": len(submissions)},
            {"plan_assignments": len(plan.get("assignments", []))},
            cost=5,
        )

        if not submissions:
            # Return empty draft if no submissions
            empty = SwarmMergedDraft(
                run_id=run_id,
                course_id=course_id,
                plan_aligned=True,
                total_submissions=0,
                total_workers=0,
                parallel_wall_time_ms=0.0,
                sequential_estimate_ms=0.0,
                speedup_factor=1.0,
                assignment_summaries=[],
                worker_results=[],
                similarity_flags=[],
                governance_audit_entries=0,
                assembled_at=datetime.utcnow().isoformat(),
            )
            return empty

        # ── Sequential baseline ────────────────────────────────────────────
        seq_time_ms = await run_sequential_baseline(submissions)

        # ── Fan-Out: parallel gather with bounded concurrency semaphore ────────
        parallel_start = time.perf_counter()
        sem = asyncio.Semaphore(self.concurrency_limit)

        async def bounded_worker(s, subs, idx):
            async with sem:
                return await swarm_worker(s, subs, idx)

        tasks = [
            bounded_worker(sub, submissions, i)
            for i, sub in enumerate(submissions)
        ]
        results: List[WorkerResult] = await asyncio.gather(*tasks)
        parallel_ms = (time.perf_counter() - parallel_start) * 1000

        # ── Audit individual workers ───────────────────────────────────────
        for r in results:
            self.runtime.log_step(
                run_id, r.worker_id, "worker_complete",
                {"submission_id": r.submission_id, "student": r.student_name},
                {
                    "final_marks": r.final_marks,
                    "plagiarism_held": r.plagiarism_held,
                    "wall_time_ms": r.wall_time_ms,
                },
                cost=3,
            )

        # ── Fan-In: merge ──────────────────────────────────────────────────
        draft = self._merge_results(plan, list(results), run_id, parallel_ms, seq_time_ms)

        # ── Checkpoint ────────────────────────────────────────────────────
        self.runtime.checkpoint(run_id, "swarm_complete", {
            "total_submissions": draft.total_submissions,
            "speedup_factor": draft.speedup_factor,
            "similarity_flags": len(draft.similarity_flags),
        })

        self.runtime.log_step(
            run_id, "SwarmCoordinator", "swarm_complete",
            {"parallel_ms": round(parallel_ms, 2), "sequential_ms": round(seq_time_ms, 2)},
            {"speedup": draft.speedup_factor, "plan_aligned": draft.plan_aligned},
            cost=5,
        )

        return draft

    def run(self, course_id: int, faculty_id: int, run_id: Optional[str] = None) -> SwarmMergedDraft:
        """Synchronous wrapper for use in non-async contexts (REST route, tests)."""
        return asyncio.run(self.run_async(course_id, faculty_id, run_id))


# Alias for backward-compatibility with capstone & tests
SwarmPipeline = SwarmCoordinator
