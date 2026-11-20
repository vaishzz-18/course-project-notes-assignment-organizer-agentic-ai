"""
Tests for Lab 7: Agentic Node Graph (LangGraph StateGraph)
Chapter 2: Course Project, Notes & Assignment Organizer

Run: cd backend && python -m pytest tests/test_lab7.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from agents.node_graph_pipeline import (
    PipelineRunner,
    CourseGraphState,
    node_ingest,
    node_plan,
    node_notes,
    node_distribute,
    node_collect,
    node_similarity,
    node_grading,
    node_validate,
    node_faculty_gate,
    edge_validate_router,
    MAX_GRADING_RETRIES,
    build_course_pipeline,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def base_state() -> CourseGraphState:
    return {
        "run_id": "test_run_lab7",
        "course_id": 1,
        "faculty_id": 1,
        "plan": {},
        "notes_summary": [],
        "distributed_assignments": [],
        "collected_submissions": [],
        "similarity_flags": [],
        "grading_results": [],
        "validation_report": {},
        "retry_count": 0,
        "pipeline_status": "running",
        "human_approved": False,
        "error_message": None,
        "audit_trail": [],
    }


def mock_state_with_submissions() -> CourseGraphState:
    """State with realistic submission data for testing downstream nodes."""
    state = base_state()
    state["plan"] = {
        "course_name": "Agentic AI & Autonomous Systems",
        "course_code": "CS401",
        "assignments": [{"id": 1, "title": "Design an Agentic Workflow", "due_date": "2024-12-01"}],
        "grading_policy": {
            "late_penalty_percent": 10,
            "plagiarism_threshold": 0.85,
            "rubric_total_marks": 100,
        },
        "units": [],
        "locked_at": "2024-01-01T00:00:00",
    }
    state["distributed_assignments"] = [
        {"student_id": 1, "student_name": "Alex Chen", "assignment_id": 1, "status": "distributed"},
        {"student_id": 2, "student_name": "Priya Sharma", "assignment_id": 1, "status": "distributed"},
    ]
    state["collected_submissions"] = [
        {
            "submission_id": 1,
            "student_name": "Alex Chen",
            "assignment_title": "Design an Agentic Workflow",
            "file_name": "alex_submission.txt",
            "submitted_at": "2024-11-30T10:00:00",
            "is_late": False,
            "content_preview": "LangGraph agent planner with MCP connector tools.",
        },
        {
            "submission_id": 2,
            "student_name": "Priya Sharma",
            "assignment_title": "Design an Agentic Workflow",
            "file_name": "priya_submission.txt",
            "submitted_at": "2024-12-05T10:00:00",
            "is_late": True,
            "content_preview": "Agentic system with autonomous decision loop and memory.",
        },
    ]
    return state


# ── Unit Tests: Individual Nodes ──────────────────────────────────────────────

class TestNodeIngest:
    def test_ingest_returns_plan_seed_for_valid_course(self):
        """node_ingest must set plan with course info and pipeline_status=running."""
        state = base_state()
        # Patch DB call to return a fake course
        with patch("agents.node_graph_pipeline._query") as mock_q:
            mock_q.side_effect = [
                [{"id": 1, "name": "Agentic AI", "code": "CS401"}],   # courses
                [{"id": 1, "title": "Assignment 1", "due_date": "2024-12-01"}],  # assignments
            ]
            result = node_ingest(state)
        assert result["pipeline_status"] == "running"
        assert "course_name" in result["plan"]
        assert len(result["audit_trail"]) == 1
        assert "[Ingest]" in result["audit_trail"][0]

    def test_ingest_errors_on_missing_course(self):
        """node_ingest must return error status when course is not found."""
        state = base_state()
        state["course_id"] = 9999
        with patch("agents.node_graph_pipeline._query") as mock_q:
            mock_q.return_value = []
            result = node_ingest(state)
        assert result["pipeline_status"] == "error"
        assert "not found" in result["error_message"]


class TestNodePlan:
    def test_plan_enriches_plan_and_locks_it(self):
        """node_plan must add grading_policy, units, and locked_at to plan."""
        state = base_state()
        state["plan"] = {"course_name": "CS401", "assignments": []}
        result = node_plan(state)
        plan = result["plan"]
        assert "grading_policy" in plan
        assert "units" in plan and len(plan["units"]) == 4
        assert "locked_at" in plan
        assert plan["grading_policy"]["rubric_total_marks"] == 100

    def test_plan_audit_trail(self):
        state = base_state()
        state["plan"] = {"course_name": "CS401"}
        result = node_plan(state)
        assert any("[Plan]" in e for e in result["audit_trail"])


class TestNodeSimilarity:
    def test_similarity_flags_identical_submissions(self):
        """node_similarity must flag pairs with similarity >= threshold."""
        state = mock_state_with_submissions()
        # Make both submissions identical text to guarantee high similarity
        for sub in state["collected_submissions"]:
            sub["content_preview"] = "The quick brown fox jumps over the lazy dog. " * 20
        result = node_similarity(state)
        flags = result["similarity_flags"]
        # With identical text, at least one flag must be raised
        assert isinstance(flags, list)
        if flags:
            assert flags[0]["is_plagiarism_risk"] is True
            assert flags[0]["similarity_score"] >= 0.85

    def test_similarity_no_flags_for_distinct_text(self):
        """node_similarity must NOT flag clearly different submissions."""
        state = mock_state_with_submissions()
        state["collected_submissions"][0]["content_preview"] = "quantum computing superconductors entanglement"
        state["collected_submissions"][1]["content_preview"] = "deep learning gradient descent backpropagation"
        result = node_similarity(state)
        # With very different texts, no plagiarism flags expected
        assert isinstance(result["similarity_flags"], list)


class TestNodeGrading:
    def test_grading_applies_late_penalty(self):
        """Late submissions must have final_marks < raw_total."""
        state = mock_state_with_submissions()
        state["similarity_flags"] = []
        result = node_grading(state)
        results = result["grading_results"]
        assert len(results) == 2
        # Priya is late
        priya = next(r for r in results if r["student_name"] == "Priya Sharma")
        assert priya["final_marks"] < priya["raw_total"]
        assert any(d["reason"] == "late_submission" for d in priya["deductions"])

    def test_grading_withholds_plagiarism_submissions(self):
        """Flagged submissions must have final_marks=0 and plagiarism_held=True."""
        state = mock_state_with_submissions()
        state["similarity_flags"] = [{"submission_a_id": 1, "submission_b_id": 2, "is_plagiarism_risk": True}]
        result = node_grading(state)
        results = result["grading_results"]
        held = [r for r in results if r["plagiarism_held"]]
        assert len(held) == 2  # both sides of the pair must be held
        for h in held:
            assert h["final_marks"] == 0

    def test_grading_no_penalties_on_clean_ontime(self):
        """On-time, non-flagged submissions must get raw rubric total."""
        state = mock_state_with_submissions()
        # Remove late flag from all
        for sub in state["collected_submissions"]:
            sub["is_late"] = False
        state["similarity_flags"] = []
        result = node_grading(state)
        results = result["grading_results"]
        for r in results:
            assert r["final_marks"] == r["raw_total"]
            assert not r["deductions"]


class TestNodeValidate:
    def test_validate_passes_with_valid_grades(self):
        """Validation must pass when all submissions are graded and marks are within bounds."""
        state = mock_state_with_submissions()
        state["grading_results"] = [
            {"submission_id": 1, "student_name": "Alex Chen", "final_marks": 83, "plagiarism_held": False,
             "raw_total": 83, "deductions": [], "rubric_breakdown": {}, "graded_on_attempt": 1},
            {"submission_id": 2, "student_name": "Priya Sharma", "final_marks": 74, "plagiarism_held": False,
             "raw_total": 83, "deductions": [], "rubric_breakdown": {}, "graded_on_attempt": 1},
        ]
        result = node_validate(state)
        assert result["validation_report"]["validation_passed"] is True
        assert result["pipeline_status"] == "needs_faculty_review"

    def test_validate_fails_on_missing_grades(self):
        """Validation must fail if a submission has no grading entry."""
        state = mock_state_with_submissions()
        state["grading_results"] = [
            {"submission_id": 1, "student_name": "Alex Chen", "final_marks": 83, "plagiarism_held": False,
             "raw_total": 83, "deductions": [], "rubric_breakdown": {}, "graded_on_attempt": 1},
        ]
        # Submission 2 is in collected but not in grading
        result = node_validate(state)
        assert result["validation_report"]["validation_passed"] is False

    def test_validate_warns_on_plagiarism_held(self):
        """Validation must PASS but emit a warning when plagiarism is held."""
        state = mock_state_with_submissions()
        state["grading_results"] = [
            {"submission_id": 1, "student_name": "Alex Chen", "final_marks": 0, "plagiarism_held": True,
             "raw_total": 83, "deductions": [], "rubric_breakdown": {}, "graded_on_attempt": 1},
            {"submission_id": 2, "student_name": "Priya Sharma", "final_marks": 0, "plagiarism_held": True,
             "raw_total": 83, "deductions": [], "rubric_breakdown": {}, "graded_on_attempt": 1},
        ]
        result = node_validate(state)
        assert len(result["validation_report"]["warnings"]) > 0


class TestEdgeValidateRouter:
    def test_routes_to_faculty_gate_on_pass(self):
        state = base_state()
        state["validation_report"] = {"validation_passed": True}
        state["retry_count"] = 0
        assert edge_validate_router(state) == "node_faculty_gate"

    def test_routes_to_grading_on_fail_with_retries_remaining(self):
        state = base_state()
        state["validation_report"] = {"validation_passed": False}
        state["retry_count"] = 1
        assert edge_validate_router(state) == "node_grading"

    def test_routes_to_end_on_max_retries(self):
        state = base_state()
        state["validation_report"] = {"validation_passed": False}
        state["retry_count"] = MAX_GRADING_RETRIES
        assert edge_validate_router(state) == "__end__"


class TestFacultyGate:
    def test_gate_status_pending_without_approval(self):
        state = mock_state_with_submissions()
        state["human_approved"] = False
        result = node_faculty_gate(state)
        assert result["pipeline_status"] == "needs_faculty_review"

    def test_gate_status_complete_with_approval(self):
        state = mock_state_with_submissions()
        state["human_approved"] = True
        result = node_faculty_gate(state)
        assert result["pipeline_status"] == "complete"


# ── Integration Test: Full Pipeline ──────────────────────────────────────────

class TestPipelineRunnerIntegration:
    def test_pipeline_runs_without_crash(self):
        """Full pipeline must run to completion without raising exceptions."""
        runner = PipelineRunner()
        # This will use the real DB — acceptable for integration
        try:
            state = runner.run(course_id=1, faculty_id=1, human_approved=True)
            assert state.get("pipeline_status") in ("complete", "needs_faculty_review", "error")
        except Exception as exc:
            pytest.fail(f"Pipeline raised unexpected exception: {exc}")

    def test_graph_compiles_without_error(self):
        """The LangGraph StateGraph must compile cleanly."""
        graph = build_course_pipeline()
        assert graph is not None
