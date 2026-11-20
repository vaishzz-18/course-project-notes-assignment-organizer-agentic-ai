"""
Acceptance Test Suite for Lab 12: Safety & Governance — Approval, Eval, Rollback
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  * Role-based confidentiality: Students see only own work; faculty sees everything.
  * Named human approval gate: require actor.can_approve and out.status == 'draft'.
  * Human faculty edits applied with explicit rationale and audit trail.
  * Versioned release publishing: each approval increments version (v1, v2...).
  * Evaluation metrics (mean, median, distribution, quarantine count) recorded per release.
  * One-click rollback: cleanly restores any historical version.
  * Unauthorized actors are strictly blocked from approving or rolling back.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from runtime.governance_release import (
    SafetyGovernanceManager,
    RoleContext,
    VersionedRelease,
    RollbackResult,
    EvaluationMetrics,
    HumanEditRecord,
)
from runtime.governed_runtime import AURAControlledRuntime


@pytest.fixture
def sample_draft():
    return {
        "course_id": 1,
        "course_code": "CS401",
        "course_name": "Agentic AI & Autonomous Systems",
        "faculty": "Dr. Vaishnavi Patel",
        "status": "draft",
        "faculty_approved": False,
        "submissions": [
            {
                "submission_id": "sub_alex_101",
                "student_id": 5,
                "student_name": "Alex Chen",
                "file_path": "uploads/alex_assign1.py",
                "late_penalty_applied": False,
            },
            {
                "submission_id": "sub_bob_102",
                "student_id": 6,
                "student_name": "Bob Miller",
                "file_path": "uploads/bob_assign1.py",
                "late_penalty_applied": True,
            },
            {
                "submission_id": "sub_charlie_103",
                "student_id": 7,
                "student_name": "Charlie Brown",
                "file_path": "uploads/charlie_assign1.py",
                "late_penalty_applied": False,
            },
        ],
        "grading_results": [
            {
                "submission_id": "sub_alex_101",
                "student_name": "Alex Chen",
                "raw_score": 92.0,
                "final_score": 92.0,
                "feedback": "Excellent LangGraph StateGraph implementation.",
                "held_for_plagiarism": False,
            },
            {
                "submission_id": "sub_bob_102",
                "student_name": "Bob Miller",
                "raw_score": 75.0,
                "final_score": 65.0,
                "feedback": "Solid ReAct loop; 10 marks deducted for late submission.",
                "held_for_plagiarism": False,
            },
            {
                "submission_id": "sub_charlie_103",
                "student_name": "Charlie Brown",
                "raw_score": 0.0,
                "final_score": 0.0,
                "feedback": "Quarantined: High code similarity detected.",
                "held_for_plagiarism": True,
            },
        ],
        "evidence_table": [
            {"claim": "StateGraph compiles", "source": "test_graph.py:L14", "grounded": True},
        ],
        "audit_trail": [
            {"step": "swarm_eval", "status": "completed", "cost_credits": 25},
        ],
    }


@pytest.fixture
def faculty_actor():
    return RoleContext.faculty(user_id=1, name="Dr. Vaishnavi Patel")


@pytest.fixture
def student_actor():
    return RoleContext.student(user_id=5, name="Alex Chen")


@pytest.fixture
def manager():
    return SafetyGovernanceManager()


class TestLab12Confidentiality:

    def test_student_sees_only_own_submissions(self, manager, sample_draft, student_actor):
        """Students must ONLY see their own submission, never peers'."""
        filtered = manager.enforce_confidentiality(sample_draft, student_actor)

        assert len(filtered["submissions"]) == 1
        assert filtered["submissions"][0]["student_name"] == "Alex Chen"
        assert filtered["submissions"][0]["submission_id"] == "sub_alex_101"

    def test_student_grades_masked_before_approval(self, manager, sample_draft, student_actor):
        """Unapproved draft grades must show PENDING_FACULTY_APPROVAL for students."""
        filtered = manager.enforce_confidentiality(sample_draft, student_actor)

        assert len(filtered["grading_results"]) == 1
        grade = filtered["grading_results"][0]
        assert grade["student_name"] == "Alex Chen"
        assert grade["final_score"] == "PENDING_FACULTY_APPROVAL"
        assert grade["raw_score"] == "PENDING_FACULTY_APPROVAL"

    def test_student_cannot_see_evidence_or_audit_trail(self, manager, sample_draft, student_actor):
        """Internal evidence tables and audit trails must be stripped for students."""
        filtered = manager.enforce_confidentiality(sample_draft, student_actor)

        assert "evidence_table" not in filtered
        assert "audit_trail" not in filtered

    def test_faculty_sees_everything_unrestricted(self, manager, sample_draft, faculty_actor):
        """Faculty sees all submissions, grades, evidence, and audit trails."""
        filtered = manager.enforce_confidentiality(sample_draft, faculty_actor)

        assert filtered["access_level"] == "UNRESTRICTED_FACULTY_VIEW"
        assert len(filtered["submissions"]) == 3
        assert len(filtered["grading_results"]) == 3
        assert "evidence_table" in filtered
        assert "audit_trail" in filtered

    def test_hod_sees_everything_unrestricted(self, manager, sample_draft):
        """Head of Department has same unrestricted access as faculty."""
        hod = RoleContext.hod(user_id=99, name="Head of Department")
        filtered = manager.enforce_confidentiality(sample_draft, hod)

        assert filtered["access_level"] == "UNRESTRICTED_FACULTY_VIEW"
        assert len(filtered["submissions"]) == 3


class TestLab12ApprovalGate:

    def test_unauthorized_student_blocked_from_approving(self, manager, sample_draft):
        """Strict hard stop: require actor.can_approve raises PermissionError for students."""
        student = RoleContext.student(user_id=9, name="Intruder Student")

        with pytest.raises(PermissionError, match="cannot approve"):
            manager.review_and_approve(sample_draft, student)

    def test_faculty_can_approve_draft(self, manager, sample_draft, faculty_actor):
        """Named faculty can approve a draft and transition it to published status."""
        release = manager.review_and_approve(sample_draft, faculty_actor)

        assert isinstance(release, VersionedRelease)
        assert release.status == "published"
        assert release.approved_by == "Dr. Vaishnavi Patel"
        assert release.version == 1
        assert release.workspace_snapshot["status"] == "published"
        assert release.workspace_snapshot["faculty_approved"] is True

    def test_non_draft_status_rejected(self, manager, faculty_actor):
        """Cannot approve a workspace that is already published."""
        already_published = {"status": "published", "course_id": 99, "course_code": "XX"}

        with pytest.raises(ValueError, match="Cannot approve workspace"):
            manager.review_and_approve(already_published, faculty_actor)

    def test_human_edits_applied_with_rationale(self, manager, sample_draft, faculty_actor):
        """Faculty human edits override agent scores with explicit recorded rationale."""
        edits = [
            {
                "submission_id": "sub_bob_102",
                "new_score": 75.0,
                "reason": "Medical leave waiver: late penalty reversed.",
            }
        ]

        release = manager.review_and_approve(sample_draft, faculty_actor, human_edits=edits)

        assert len(release.human_edits) == 1
        edit = release.human_edits[0]
        assert isinstance(edit, HumanEditRecord)
        assert edit.student_name == "Bob Miller"
        assert edit.original_score == 65.0
        assert edit.adjusted_score == 75.0
        assert edit.faculty_reason == "Medical leave waiver: late penalty reversed."
        assert edit.edited_by == "Dr. Vaishnavi Patel"

        # Confirm score actually changed in workspace
        bob_grade = next(
            g for g in release.workspace_snapshot["grading_results"]
            if g["submission_id"] == "sub_bob_102"
        )
        assert bob_grade["final_score"] == 75.0
        assert bob_grade["faculty_override"] is True


class TestLab12Metrics:

    def test_evaluation_metrics_recorded_on_publish(self, manager, sample_draft, faculty_actor):
        """Publish must calculate and record evaluation metrics."""
        release = manager.review_and_approve(sample_draft, faculty_actor)

        m = release.metrics
        assert isinstance(m, EvaluationMetrics)
        assert m.total_submissions == 3
        assert m.average_score > 0.0
        assert m.median_score > 0.0
        assert m.highest_score == 92.0
        assert m.lowest_score == 0.0
        assert m.plagiarism_quarantine_count == 1
        assert m.late_penalty_count == 1
        assert isinstance(m.grade_distribution, dict)
        assert sum(m.grade_distribution.values()) > 0


class TestLab12Versioning:

    def test_version_increments_on_successive_publishes(self, manager, sample_draft, faculty_actor):
        """Each approval must produce an incremented version number v1, v2, ..."""
        v1 = manager.review_and_approve(sample_draft, faculty_actor)
        assert v1.version == 1
        assert manager.active_versions[1] == 1

        # Need a fresh draft for v2
        draft2 = dict(sample_draft)
        draft2["status"] = "draft"
        draft2["faculty_approved"] = False
        v2 = manager.review_and_approve(draft2, faculty_actor)
        assert v2.version == 2
        assert manager.active_versions[1] == 2

    def test_version_history_stored(self, manager, sample_draft, faculty_actor):
        """All published versions must be retrievable from version history."""
        manager.review_and_approve(sample_draft, faculty_actor)

        draft2 = dict(sample_draft)
        draft2["status"] = "draft"
        draft2["faculty_approved"] = False
        manager.review_and_approve(draft2, faculty_actor)

        versions = manager.version_history[1]
        assert len(versions) == 2
        assert 1 in versions
        assert 2 in versions


class TestLab12Rollback:

    def test_one_click_rollback_restores_version(self, manager, sample_draft, faculty_actor):
        """1-click rollback cleanly restores a prior version."""
        v1 = manager.review_and_approve(sample_draft, faculty_actor)
        alex_v1_score = v1.workspace_snapshot["grading_results"][0]["final_score"]

        # Publish v2 with different score
        draft2 = dict(sample_draft)
        draft2["status"] = "draft"
        draft2["faculty_approved"] = False
        manager.review_and_approve(
            draft2, faculty_actor,
            human_edits=[{"submission_id": "sub_alex_101", "new_score": 98.0, "reason": "Bonus"}]
        )
        assert manager.active_versions[1] == 2

        # Rollback to v1
        result = manager.rollback(course_id=1, target_version=1, actor=faculty_actor)

        assert isinstance(result, RollbackResult)
        assert result.active_version == 1
        assert result.rolled_back_by == "Dr. Vaishnavi Patel"
        restored_score = result.restored_workspace["grading_results"][0]["final_score"]
        assert restored_score == alex_v1_score

    def test_unauthorized_rollback_blocked(self, manager, sample_draft, faculty_actor):
        """Students cannot trigger rollback."""
        manager.review_and_approve(sample_draft, faculty_actor)

        student = RoleContext.student(user_id=5, name="Alex Chen")
        with pytest.raises(PermissionError, match="cannot execute rollback"):
            manager.rollback(course_id=1, target_version=1, actor=student)

    def test_rollback_to_nonexistent_version_raises(self, manager, sample_draft, faculty_actor):
        """Rollback to a version that does not exist must raise ValueError."""
        manager.review_and_approve(sample_draft, faculty_actor)

        with pytest.raises(ValueError, match="Version not found"):
            manager.rollback(course_id=1, target_version=999, actor=faculty_actor)


class TestLab12RuntimeAudit:

    def test_approval_logged_to_runtime(self, sample_draft, faculty_actor):
        """Governance publish event must be logged in AURAControlledRuntime audit."""
        runtime = AURAControlledRuntime()
        mgr = SafetyGovernanceManager(runtime=runtime)

        mgr.review_and_approve(sample_draft, faculty_actor)

        governance_steps = [
            s for s in runtime.in_memory_audit
            if s.agent_name == "SafetyGovernanceManager"
        ]
        assert len(governance_steps) >= 1
        publish_step = next(s for s in governance_steps if s.action == "publish_approved_version")
        assert publish_step.output_data["status"] == "published"

    def test_rollback_logged_to_runtime(self, sample_draft, faculty_actor):
        """Rollback event must be logged in AURAControlledRuntime audit."""
        runtime = AURAControlledRuntime()
        mgr = SafetyGovernanceManager(runtime=runtime)

        mgr.review_and_approve(sample_draft, faculty_actor)
        mgr.rollback(course_id=1, target_version=1, actor=faculty_actor)

        rollback_steps = [
            s for s in runtime.in_memory_audit
            if s.action == "rollback_version"
        ]
        assert len(rollback_steps) == 1
        assert rollback_steps[0].output_data["status"] == "restored"


class TestLab12ApiIntegration:

    def test_lab12_demo_endpoint(self):
        """FastAPI route /lab12/demo must return a successful governance walkthrough."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab12/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["lab"] == "Lab 12: Safety & Governance — Approval, Eval, Rollback"

        steps = data["steps"]
        # Confidentiality enforced
        assert steps["step1_student_draft_confidentiality"]["visible_submissions_count"] == 1
        assert steps["step1_student_draft_confidentiality"]["evidence_table_stripped"] is True
        # Faculty full view
        assert steps["step2_faculty_unrestricted_view"]["visible_submissions_count"] == 3
        # Unauthorized blocked
        assert steps["step3_unauthorized_student_blocked"]["hard_stop_enforced"] is True
        # v1 published
        assert steps["step4_published_release_v1"]["version"] == 1
        assert steps["step4_published_release_v1"]["human_edits_applied"] >= 1
        # Rollback
        assert steps["step7_one_click_rollback_to_v1"]["active_version_now"] == 1
