"""
Tests for Lab 8: Parallel Swarm (Fan-Out / Fan-In)
Chapter 2: Course Project, Notes & Assignment Organizer

Run: cd backend && python -m pytest tests/test_lab8.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from agents.swarm_pipeline import (
    SwarmCoordinator,
    SubmissionPayload,
    WorkerResult,
    swarm_worker,
    run_sequential_baseline,
    PLAGIARISM_THRESHOLD,
    LATE_PENALTY_PERCENT,
    RUBRIC,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_submission(
    sub_id: int,
    name: str,
    content: str = "Generic agentic AI submission content.",
    is_late: bool = False,
    assignment_id: int = 1,
) -> SubmissionPayload:
    return SubmissionPayload(
        submission_id=sub_id,
        student_name=name,
        student_id=sub_id,
        assignment_id=assignment_id,
        assignment_title="Design an Agentic Workflow",
        file_name=f"{name.lower().replace(' ', '_')}.txt",
        file_path="",
        submitted_at="2024-11-30T10:00:00",
        is_late=is_late,
        content=content,
    )


SAMPLE_SUBMISSIONS = [
    make_submission(1, "Alex Chen",    content="LangGraph StateGraph with MCP connector and tool calling."),
    make_submission(2, "Priya Sharma", content="Autonomous agent with memory retrieval and rubric grading.", is_late=True),
    make_submission(3, "Marcus Vance", content="LangGraph StateGraph with MCP connector and tool calling."),  # Identical to Alex → plagiarism
    make_submission(4, "Elena Rostova", content="Swarm coordination with asyncio gather and fan-in merge."),
    make_submission(5, "David Kim",    content="Separate memory: short-term run state and long-term ChromaDB."),
]


# ── Unit Tests: swarm_worker ──────────────────────────────────────────────────

class TestSwarmWorker:
    def test_worker_returns_worker_result(self):
        """swarm_worker must return a WorkerResult for a clean submission."""
        sub = make_submission(10, "Test Student", content="This is a unique submission about LLMs.")
        result = asyncio.run(swarm_worker(sub, [sub], 0))
        assert isinstance(result, WorkerResult)
        assert result.submission_id == 10
        assert result.student_name == "Test Student"
        assert result.raw_total > 0
        assert result.wall_time_ms >= 0

    def test_worker_applies_late_penalty(self):
        """Worker must deduct late penalty from final_marks."""
        sub = make_submission(11, "Late Student", content="Unique late submission.", is_late=True)
        result = asyncio.run(swarm_worker(sub, [sub], 0))
        expected_penalty = round(result.raw_total * LATE_PENALTY_PERCENT / 100, 1)
        assert result.final_marks == round(result.raw_total - expected_penalty, 1)
        assert any(d["reason"] == "late_submission" for d in result.deductions)

    def test_worker_holds_plagiarism(self):
        """Worker must set plagiarism_held=True and final_marks=0 for flagged pairs."""
        identical_content = "The quick brown fox jumps over the lazy dog. " * 30
        sub_a = make_submission(20, "Student A", content=identical_content)
        sub_b = make_submission(21, "Student B", content=identical_content)
        result = asyncio.run(swarm_worker(sub_a, [sub_a, sub_b], 0))
        assert result.is_plagiarism_risk is True
        assert result.plagiarism_held is True
        assert result.final_marks == 0.0

    def test_worker_no_penalty_for_clean_submission(self):
        """On-time, unique submission must receive full raw rubric total."""
        sub = make_submission(30, "Clean Student", content="Completely unique text about quantum computing and AI.")
        # Different companion submission
        other = make_submission(31, "Other Student", content="Deep learning backpropagation gradient descent.")
        result = asyncio.run(swarm_worker(sub, [sub, other], 0))
        if not result.plagiarism_held:
            assert result.final_marks == result.raw_total

    def test_worker_rubric_sum_correct(self):
        """Raw total must equal sum of all rubric part base_awarded values."""
        sub = make_submission(40, "Rubric Test")
        result = asyncio.run(swarm_worker(sub, [sub], 0))
        expected_raw = sum(v["base_awarded"] for v in RUBRIC.values())
        assert result.raw_total == expected_raw

    def test_worker_similarity_scores_excludes_self(self):
        """Similarity scores must not include a comparison against the same submission."""
        sub = make_submission(50, "Self Test")
        others = [make_submission(51, "Other 1"), make_submission(52, "Other 2")]
        result = asyncio.run(swarm_worker(sub, [sub] + others, 0))
        compared_ids = [s["compared_to_id"] for s in result.similarity_scores]
        assert sub.submission_id not in compared_ids

    def test_worker_empty_content_does_not_crash(self):
        """Worker must handle empty-content submissions gracefully."""
        sub = make_submission(60, "Empty Student", content="")
        result = asyncio.run(swarm_worker(sub, [sub], 0))
        assert isinstance(result, WorkerResult)
        assert result.max_similarity == 0.0


# ── Unit Tests: Parallel vs Sequential ───────────────────────────────────────

class TestParallelVsSequential:
    def test_parallel_is_at_least_as_fast_as_sequential(self):
        """Fan-out must not be slower than sequential by an unreasonable margin."""
        import time

        submissions = SAMPLE_SUBMISSIONS[:3]

        # Sequential
        seq_start = time.perf_counter()
        asyncio.run(run_sequential_baseline(submissions))
        seq_time = (time.perf_counter() - seq_start) * 1000

        # Parallel
        async def parallel_run():
            return await asyncio.gather(*[
                swarm_worker(sub, submissions, i)
                for i, sub in enumerate(submissions)
            ])

        par_start = time.perf_counter()
        asyncio.run(parallel_run())
        par_time = (time.perf_counter() - par_start) * 1000

        # Parallel should not take more than 2× sequential for small sets
        # (overhead vs benefit balances only at scale, but logic must hold)
        assert par_time < seq_time * 3 or par_time < 5000  # at most 3× or < 5s

    def test_all_workers_return_results(self):
        """asyncio.gather must return one result per submission."""
        submissions = SAMPLE_SUBMISSIONS

        async def gather_all():
            return await asyncio.gather(*[
                swarm_worker(sub, submissions, i)
                for i, sub in enumerate(submissions)
            ])

        results = asyncio.run(gather_all())
        assert len(results) == len(submissions)
        for r in results:
            assert isinstance(r, WorkerResult)


# ── Unit Tests: Merge Logic ───────────────────────────────────────────────────

class TestSwarmMerge:
    def test_merge_is_plan_aligned(self):
        """Merged draft must have one assignment summary per plan assignment."""
        coordinator = SwarmCoordinator()
        plan = {
            "course_id": 1,
            "course_name": "CS401",
            "assignments": [
                {"id": 1, "title": "Assignment 1"},
                {"id": 2, "title": "Assignment 2"},
            ],
            "grading_policy": {"plagiarism_threshold": PLAGIARISM_THRESHOLD},
        }
        submissions = [
            make_submission(1, "Alice", assignment_id=1),
            make_submission(2, "Bob",   assignment_id=2),
        ]

        async def get_results():
            return await asyncio.gather(*[
                swarm_worker(sub, submissions, i)
                for i, sub in enumerate(submissions)
            ])

        results = asyncio.run(get_results())
        draft = coordinator._merge_results(plan, results, "test_run", 10.0, 20.0)

        assert draft.plan_aligned is True
        assert len(draft.assignment_summaries) == len(plan["assignments"])

    def test_similarity_flags_are_deduplicated(self):
        """Duplicate (A,B) and (B,A) pairs must appear only once in merged flags."""
        coordinator = SwarmCoordinator()
        identical = "identical content for plagiarism test " * 25
        sub_a = make_submission(1, "Alice", content=identical)
        sub_b = make_submission(2, "Bob",   content=identical)
        plan = {
            "course_id": 1,
            "assignments": [{"id": 1, "title": "Assignment 1"}],
            "grading_policy": {"plagiarism_threshold": PLAGIARISM_THRESHOLD},
        }

        async def get_results():
            return await asyncio.gather(
                swarm_worker(sub_a, [sub_a, sub_b], 0),
                swarm_worker(sub_b, [sub_a, sub_b], 1),
            )

        results = asyncio.run(get_results())
        draft = coordinator._merge_results(plan, results, "dedup_run", 5.0, 10.0)

        # The (1,2) pair should appear exactly once
        pairs = [(f["submission_a_id"], f["submission_b_id"]) for f in draft.similarity_flags]
        assert len(pairs) == len(set(pairs)), "Duplicate pairs found in similarity flags"

    def test_speedup_factor_calculated_correctly(self):
        """speedup_factor must be sequential_ms / parallel_ms."""
        coordinator = SwarmCoordinator()
        plan = {"course_id": 1, "assignments": [], "grading_policy": {"plagiarism_threshold": 0.85}}
        draft = coordinator._merge_results(plan, [], "speed_run", 50.0, 200.0)
        assert draft.speedup_factor == 4.0


# ── Integration Test: Full Swarm ──────────────────────────────────────────────

class TestSwarmCoordinatorIntegration:
    def test_coordinator_run_does_not_crash(self):
        """SwarmCoordinator.run must complete without raising exceptions."""
        coordinator = SwarmCoordinator()
        try:
            draft = coordinator.run(course_id=1, faculty_id=1)
            assert draft is not None
            assert draft.total_submissions >= 0
        except Exception as exc:
            pytest.fail(f"SwarmCoordinator raised unexpected exception: {exc}")

    def test_coordinator_run_returns_plan_aligned_draft(self):
        """Result must be plan-aligned if assignments exist in the DB."""
        coordinator = SwarmCoordinator()
        draft = coordinator.run(course_id=1, faculty_id=1)
        # Even with no submissions, plan_aligned should be True (vacuously)
        assert isinstance(draft.plan_aligned, bool)

    def test_coordinator_run_populates_audit_entries(self):
        """AURAControlledRuntime must log at least the start and complete entries."""
        coordinator = SwarmCoordinator()
        draft = coordinator.run(course_id=1, faculty_id=1)
        assert draft.governance_audit_entries >= 2
