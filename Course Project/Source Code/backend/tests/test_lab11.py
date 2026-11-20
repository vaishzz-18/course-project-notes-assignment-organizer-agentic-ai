"""
Acceptance Test Suite for Lab 11: SDLC Factory — Spec → Tested Output
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  • Treat the plan as a specification and output as a tested implementation.
  • A 'build' command: plan → organised course workspace + passing acceptance report.
  • Automated 12-point acceptance test suite validates spec compliance and safety.
  • Gatekeeper strictly blocks advancement to Course Faculty unless all checks pass (require report.all_pass).
  • Full provenance logged to AURAControlledRuntime.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.sdlc_factory import (
    SDLCWorkspaceFactory,
    BuildArtifact,
    AcceptanceReport,
    GateVerificationResult,
)
from runtime.governed_runtime import AURAControlledRuntime


@pytest.fixture
def plan_spec():
    return {
        "course_code": "CS401",
        "course_name": "Agentic AI & Autonomous Systems",
        "faculty": "Dr. Vaishnavi Patel",
        "max_marks": 100.0,
        "units": [
            {"unit": "Unit 1", "title": "ReAct Cognitive Loops & Planner Engines"},
            {"unit": "Unit 2", "title": "Tool-Using Agents & Zero-Hallucination Math"},
            {"unit": "Unit 3", "title": "LangGraph StateGraphs & Back-Edges"},
            {"unit": "Unit 4", "title": "Parallel Multi-Agent Swarms"}
        ],
        "assignments": [
            {
                "id": 1,
                "title": "Assignment 1: Agentic Workflow Architecture",
                "max_marks": 100.0,
                "due_date": "2026-10-15T23:59:59Z"
            }
        ],
        "milestones": [
            {"checkpoint": 1, "title": "Core Agentic Architecture", "week": 4},
            {"checkpoint": 2, "title": "Swarm Benchmarking", "week": 8}
        ]
    }


class TestLab11SDLCFactory:

    def test_build_produces_complete_artifact_from_plan_spec(self, plan_spec):
        """Build command must transform plan spec into an assembled workspace artifact."""
        runtime = AURAControlledRuntime()
        factory = SDLCWorkspaceFactory(runtime=runtime)

        artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1)

        assert artifact.build_id.startswith("build_cs401_")
        assert artifact.course_code == "CS401"
        assert artifact.build_time_ms > 0
        assert artifact.workspace["status"] == "draft_pending_faculty_review"
        assert len(artifact.workspace["submissions"]) >= 4
        assert len(artifact.workspace["grading_results"]) >= 4
        assert "evidence_table" in artifact.workspace

    def test_acceptance_suite_12_points_pass_on_clean_build(self, plan_spec):
        """Clean build must pass all 12 acceptance checks with a green report."""
        runtime = AURAControlledRuntime()
        factory = SDLCWorkspaceFactory(runtime=runtime)

        artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1)
        report = factory.run_acceptance_suite(artifact, plan_spec=plan_spec)

        assert report.total_tests == 12
        assert report.passed_count == 12
        assert report.failed_count == 0
        assert report.all_pass is True
        assert report.passed_gate_to_human is True

        # Verify specific test categories
        categories = {t.category for t in report.tests}
        assert "SPEC_COMPLIANCE" in categories
        assert "RUBRIC_INTEGRITY" in categories
        assert "DEADLINE_COMPLIANCE" in categories
        assert "GROUNDING_EVIDENCE" in categories
        assert "GOVERNANCE_SAFETY" in categories

    def test_acceptance_gate_blocks_human_review_if_any_test_fails(self, plan_spec):
        """Strict gatekeeper: require report.all_pass before faculty review."""
        runtime = AURAControlledRuntime()
        factory = SDLCWorkspaceFactory(runtime=runtime)

        artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1)

        # 1. Clean artifact passes gate
        clean_gate = factory.verify_and_advance_to_faculty(artifact)
        assert clean_gate.gate_status == "ADVANCED_TO_FACULTY"
        assert clean_gate.authorized_for_faculty_review is True

        # 2. Corrupt artifact with rubric overflow
        corrupted = artifact.model_copy(deep=True)
        corrupted.workspace["grading_results"][0]["final_score"] = 150.0  # Rubric max is 100
        corrupted_report = factory.run_acceptance_suite(corrupted, plan_spec=plan_spec)
        assert corrupted_report.all_pass is False

        blocked_gate = factory.verify_and_advance_to_faculty(corrupted)
        assert blocked_gate.gate_status == "BLOCKED_BY_ACCEPTANCE_GATE"
        assert blocked_gate.authorized_for_faculty_review is False
        assert "blocked" in blocked_gate.reason.lower()

    def test_spec_drift_detected_by_sdlc_factory(self, plan_spec):
        """If workspace deviates from locked plan specification, factory flags drift."""
        runtime = AURAControlledRuntime()
        factory = SDLCWorkspaceFactory(runtime=runtime)

        artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1)

        # Alter spec course code to simulate drift
        drifted_spec = copy_spec = dict(plan_spec)
        drifted_spec["course_code"] = "CS999_UNAPPROVED"

        report = factory.run_acceptance_suite(artifact, plan_spec=drifted_spec)
        assert report.all_pass is False

        spec_test = next(t for t in report.tests if t.test_id == "SPEC-01")
        assert spec_test.passed is False

    def test_sdlc_factory_runtime_audit_provenance(self, plan_spec):
        """Factory build must record provenance entries in AURAControlledRuntime."""
        runtime = AURAControlledRuntime()
        factory = SDLCWorkspaceFactory(runtime=runtime)

        artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1)

        assert len(runtime.in_memory_audit) >= 1
        build_step = next(s for s in runtime.in_memory_audit if s.agent_name == "SDLCWorkspaceFactory")
        assert build_step.action == "build_artifact"
        assert build_step.output_data["build_id"] == artifact.build_id


class TestLab11ApiIntegration:

    def test_lab11_demo_endpoint(self):
        """FastAPI route /lab11/demo must return all acceptance criteria passed."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab11/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["lab"] == "Lab 11: SDLC Factory — Spec → Tested Output"
        assert data["acceptance_criteria_passed"] is True
        assert data["criteria_detail"]["automated_12_point_suite_executed"] is True
        assert data["criteria_detail"]["clean_artifact_advanced_to_faculty"] is True
        assert data["criteria_detail"]["corrupted_artifact_blocked_at_gate"] is True
