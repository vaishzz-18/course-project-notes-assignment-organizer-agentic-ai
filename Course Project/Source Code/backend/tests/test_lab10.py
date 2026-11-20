"""
Acceptance Test Suite for Lab 10: Ops Resilience — Validate, Diagnose, Fix
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  • When a check fails (draft grade > rubric max; unpenalized late submission),
    the agent diagnoses the exact failing constraint.
  • Regenerates ONLY the offending part — rebuilding everything wastes budget.
  • Injected faults are detected and fixed within the retry budget.
  • On budget exhaustion, escalates to course faculty with diagnosis.
  • Full provenance logged to AURAControlledRuntime.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.resilience_coordinator import (
    OpsResilienceCoordinator,
    ValidationReport,
    SelfHealingResult,
    FailingItem,
)
from runtime.governed_runtime import AURAControlledRuntime


@pytest.fixture
def baseline_draft():
    return {
        "course_id": 1,
        "course_code": "CS401",
        "assignment_id": 1,
        "assignment_title": "Assignment 1: Agentic Workflow Architecture",
        "status": "draft",
        "faculty_approved": False,
        "submissions": [
            {
                "id": "sub_alex_1",
                "student_name": "Alex Chen",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.08,
                "content": "Clean LangGraph StateGraph implementation with ReAct loops."
            },
            {
                "id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.11,
                "content": "Parallel swarm worker pool with plan-aligned fan-in merge."
            },
            {
                "id": "sub_david_3",
                "student_name": "David Kim",
                "is_late": True,
                "late_penalty_applied": True,
                "similarity_score": 0.09,
                "content": "Pydantic typed tools with deadline and rubric arithmetic."
            }
        ],
        "grading_results": [
            {
                "submission_id": "sub_alex_1",
                "student_name": "Alex Chen",
                "final_score": 92.0,
                "raw_score": 92.0,
                "feedback": "Outstanding implementation of LangGraph nodes."
            },
            {
                "submission_id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "final_score": 88.0,
                "raw_score": 88.0,
                "feedback": "Excellent concurrency speedup benchmark."
            },
            {
                "submission_id": "sub_david_3",
                "student_name": "David Kim",
                "final_score": 76.5,
                "raw_score": 85.0,
                "feedback": "Clean typed tools; 10% late penalty applied."
            }
        ]
    }


class TestLab10ValidationAndDiagnosis:

    def test_baseline_draft_passes_validation(self, baseline_draft):
        """Baseline compliant draft must pass all 4 Chapter 2 invariants."""
        coordinator = OpsResilienceCoordinator()
        report = coordinator.validate(baseline_draft, {"max_marks": 100.0})

        assert report.passed is True
        assert report.failing_checks == 0
        assert len(report.failing_items) == 0

    def test_detects_and_diagnoses_rubric_overflow(self, baseline_draft):
        """Grade exceeding rubric max (e.g. 120 / 100) must be detected and isolated."""
        coordinator = OpsResilienceCoordinator()
        corrupted = coordinator.inject_faults(baseline_draft, ["rubric_overflow"])

        report = coordinator.validate(corrupted, {"max_marks": 100.0})

        assert report.passed is False
        overflow_items = [f for f in report.failing_items if f.entity_type == "grade"]
        assert len(overflow_items) == 1
        assert overflow_items[0].observed_value == 125.0
        assert "a draft grade never exceeds the rubric maximum" in overflow_items[0].failing_rule

    def test_detects_and_diagnoses_unflagged_late_submission(self, baseline_draft):
        """Late submission without penalty flag must be detected and isolated."""
        coordinator = OpsResilienceCoordinator()
        corrupted = coordinator.inject_faults(baseline_draft, ["unflagged_late_submission"])

        report = coordinator.validate(corrupted, {"max_marks": 100.0})

        assert report.passed is False
        late_items = [f for f in report.failing_items if "late" in f.failing_rule]
        assert len(late_items) >= 1
        assert late_items[0].entity_type == "submission"

    def test_detects_and_diagnoses_missing_similarity_score(self, baseline_draft):
        """Submission missing similarity metric must be detected and isolated."""
        coordinator = OpsResilienceCoordinator()
        corrupted = coordinator.inject_faults(baseline_draft, ["missing_similarity_score"])

        report = coordinator.validate(corrupted, {"max_marks": 100.0})

        assert report.passed is False
        sim_items = [f for f in report.failing_items if f.entity_type == "similarity"]
        assert len(sim_items) == 1
        assert sim_items[0].observed_value is None

    def test_detects_unapproved_publish_attempt(self, baseline_draft):
        """Publishing without faculty sign-off must be caught by governance check."""
        coordinator = OpsResilienceCoordinator()
        corrupted = coordinator.inject_faults(baseline_draft, ["unapproved_publish"])

        report = coordinator.validate(corrupted, {"max_marks": 100.0})

        assert report.passed is False
        gov_items = [f for f in report.failing_items if f.entity_type == "governance"]
        assert len(gov_items) == 1
        assert "no grade is published without faculty approval" in gov_items[0].failing_rule


class TestLab10SelfHealingLoop:

    def test_targeted_repair_modifies_only_offending_item(self, baseline_draft):
        """Targeted repair must fix the failing item while leaving compliant items unchanged."""
        coordinator = OpsResilienceCoordinator()
        corrupted = coordinator.inject_faults(baseline_draft, ["rubric_overflow"])

        report = coordinator.validate(corrupted, {"max_marks": 100.0})
        repaired, repair_steps = coordinator.targeted_regenerate(
            draft=corrupted,
            failing_items=report.failing_items,
            plan={"max_marks": 100.0}
        )

        # Offending item repaired
        alex_grade = next(g for g in repaired["grading_results"] if g["submission_id"] == "sub_alex_1")
        assert alex_grade["final_score"] <= 100.0

        # Compliant items untouched
        priya_grade = next(g for g in repaired["grading_results"] if g["submission_id"] == "sub_priya_2")
        assert priya_grade["final_score"] == 88.0

        david_grade = next(g for g in repaired["grading_results"] if g["submission_id"] == "sub_david_3")
        assert david_grade["final_score"] == 76.5

    def test_self_healing_resolves_all_faults_within_budget(self, baseline_draft):
        """Self-healing loop must repair multiple concurrent faults within retry budget."""
        runtime = AURAControlledRuntime()
        coordinator = OpsResilienceCoordinator(retry_budget=3, runtime=runtime)

        corrupted = coordinator.inject_faults(
            baseline_draft,
            ["rubric_overflow", "unflagged_late_submission", "missing_similarity_score"]
        )

        result = coordinator.self_healing_loop(
            draft=corrupted,
            plan={"max_marks": 100.0},
            run_id="test_run_resilience"
        )

        assert result.status == "RESOLVED"
        assert result.initial_passed is False
        assert result.final_passed is True
        assert result.attempts_used <= 3
        assert len(result.repair_log) >= 3
        assert result.escalation is None

        # Verify audit logging
        assert len(runtime.in_memory_audit) >= 1
        step = runtime.in_memory_audit[-1]
        assert step.agent_name == "OpsResilienceCoordinator"

    def test_budget_exhaustion_escalates_to_human(self, baseline_draft):
        """When budget is exhausted, coordinator escalates to named human faculty authority."""
        runtime = AURAControlledRuntime()
        # Budget of 0 attempts guarantees immediate exhaustion
        coordinator = OpsResilienceCoordinator(retry_budget=0, runtime=runtime)

        corrupted = coordinator.inject_faults(baseline_draft, ["rubric_overflow"])

        result = coordinator.self_healing_loop(
            draft=corrupted,
            plan={"max_marks": 100.0},
            run_id="test_run_escalation"
        )

        assert result.status == "ESCALATED"
        assert result.final_passed is False
        assert result.escalation is not None
        assert "Course Faculty" in result.escalation.escalated_to
        assert len(result.escalation.unresolved_items) >= 1


class TestLab10ApiIntegration:

    def test_lab10_demo_endpoint(self):
        """FastAPI route /lab10/demo must return all acceptance criteria passed."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab10/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["lab"] == "Lab 10: Ops Resilience — Validate, Diagnose, Fix"
        assert data["acceptance_criteria_passed"] is True
        assert data["criteria_detail"]["injected_faults_detected"] is True
        assert data["criteria_detail"]["self_healing_succeeded"] is True
        assert data["criteria_detail"]["final_validation_passed"] is True
