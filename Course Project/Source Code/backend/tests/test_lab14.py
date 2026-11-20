"""
Acceptance Test Suite for Lab 14: Capstone — Full Team-Owned Deployed System
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  * All 14 labs integrated into a single CapstoneSystem.
  * system.run(request) produces a CapstoneArtifact with 9 pipeline stages.
  * Faculty approval gate: approve → publish lifecycle works.
  * Dashboard returns all 4 panels: notes, submissions, grades, milestones.
  * One-click rollback works cleanly.
  * Validation report passes all acceptance checks.
  * Complete audit trail is maintained.
  * Unapproved artifacts cannot be published.
  * Unknown sessions raise KeyError.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from runtime.capstone_system import (
    CapstoneSystem,
    CapstoneRequest,
    CapstoneArtifact,
    DashboardView,
    SystemStatus,
)


@pytest.fixture
def system():
    return CapstoneSystem()


@pytest.fixture
def request_obj():
    return CapstoneRequest(
        course_id=1,
        faculty_id=1,
        faculty_name="Dr. Sarah Chen",
        request_text="Test request.",
        domain="theory",
    )


class TestCapstoneSystemDeploy:

    def test_system_initializes_to_ready(self, system):
        """CapstoneSystem.status starts at READY after deployment."""
        assert system.status == SystemStatus.READY

    def test_system_status_shows_14_labs(self, system):
        """get_system_status reports 14 integrated labs."""
        status = system.get_system_status()
        assert status["labs_integrated"] == 14

    def test_system_status_lists_all_subsystems(self, system):
        """All 9 subsystem keys are present."""
        status = system.get_system_status()
        expected_keys = {
            "connector", "runtime", "graph_pipeline", "swarm",
            "grounding", "resilience", "sdlc_factory", "governance", "specialists",
        }
        assert set(status["subsystems"].keys()) == expected_keys


class TestCapstoneRun:

    def test_run_produces_artifact(self, system, request_obj):
        """system.run(request) returns a CapstoneArtifact."""
        artifact = system.run(request_obj)
        assert isinstance(artifact, CapstoneArtifact)
        assert artifact.session_id == request_obj.session_id

    def test_run_has_9_pipeline_stages(self, system, request_obj):
        """Pipeline runs exactly 9 stages (one per integrated lab)."""
        artifact = system.run(request_obj)
        assert artifact.metrics["total_stages"] == 9

    def test_run_workspace_has_all_sections(self, system, request_obj):
        """Workspace contains notes, assignments, submissions, grades, milestones."""
        artifact = system.run(request_obj)
        ws = artifact.workspace
        assert "notes" in ws
        assert "assignments" in ws
        assert "submissions" in ws
        assert "grades" in ws
        assert "milestones" in ws

    def test_run_validation_report_present(self, system, request_obj):
        """Run includes a validation report with acceptance checks."""
        artifact = system.run(request_obj)
        vr = artifact.validation_report
        assert "all_passed" in vr
        assert "checks" in vr
        assert len(vr["checks"]) >= 4

    def test_run_status_awaiting_review(self, system, request_obj):
        """After run, artifact status is awaiting_faculty_review."""
        artifact = system.run(request_obj)
        assert artifact.status == "awaiting_faculty_review"

    def test_run_evidence_table_has_entries(self, system, request_obj):
        """Evidence table has one entry per stage."""
        artifact = system.run(request_obj)
        assert len(artifact.evidence_table) == 9


class TestCapstoneApprovalLifecycle:

    def test_approve_changes_status(self, system, request_obj):
        """Approve changes artifact status to 'approved'."""
        artifact = system.run(request_obj)
        approved = system.approve(
            session_id=artifact.session_id,
            faculty_id=1,
            faculty_name="Dr. Sarah Chen",
        )
        assert approved.status == "approved"

    def test_publish_after_approval(self, system, request_obj):
        """Publish works only after approval and bumps version."""
        artifact = system.run(request_obj)
        system.approve(artifact.session_id, 1, "Dr. Sarah Chen")
        published = system.publish(artifact.session_id)
        assert published.status == "published"
        assert published.governance_record["version"] >= 1

    def test_publish_without_approval_raises(self, system, request_obj):
        """Cannot publish without faculty approval."""
        artifact = system.run(request_obj)
        with pytest.raises(ValueError, match="not approved"):
            system.publish(artifact.session_id)

    def test_approve_with_edits(self, system, request_obj):
        """Faculty can apply edits during approval."""
        artifact = system.run(request_obj)
        edits = {"notes": [{"unit": "Edited", "title": "Updated Notes", "version": 5}]}
        approved = system.approve(
            artifact.session_id, 1, "Dr. Sarah Chen", edits=edits,
        )
        assert approved.workspace["notes"] == edits["notes"]


class TestCapstoneRollback:

    def test_rollback_changes_status(self, system, request_obj):
        """Rollback sets status to rolled_back."""
        artifact = system.run(request_obj)
        system.approve(artifact.session_id, 1, "Dr. Sarah Chen")
        system.publish(artifact.session_id)
        rolled = system.rollback(artifact.session_id)
        assert rolled.status == "rolled_back"


class TestCapstoneDashboard:

    def test_dashboard_returns_all_panels(self, system, request_obj):
        """Dashboard has notes_portal, submission_dashboard, draft_grades_queue, milestone_tracker."""
        artifact = system.run(request_obj)
        dash = system.dashboard(artifact.session_id)
        assert isinstance(dash, DashboardView)
        dd = dash.to_dict()
        assert "notes_portal" in dd
        assert "submission_dashboard" in dd
        assert "draft_grades_queue" in dd
        assert "milestone_tracker" in dd
        assert "system_health" in dd
        assert "governance_panel" in dd


class TestCapstoneAuditTrail:

    def test_audit_trail_non_empty(self, system, request_obj):
        """After run, audit trail has entries."""
        artifact = system.run(request_obj)
        assert len(artifact.audit_trail) > 0

    def test_audit_trail_grows_on_approve(self, system, request_obj):
        """Audit trail grows when faculty approves."""
        artifact = system.run(request_obj)
        trail_before = len(system._audit_log)
        system.approve(artifact.session_id, 1, "Dr. Sarah Chen")
        assert len(system._audit_log) > trail_before


class TestCapstoneErrorHandling:

    def test_unknown_session_raises_keyerror(self, system):
        """Operations on unknown session_id raise KeyError."""
        with pytest.raises(KeyError):
            system.approve("nonexistent", 1, "Dr. X")

        with pytest.raises(KeyError):
            system.publish("nonexistent")

        with pytest.raises(KeyError):
            system.rollback("nonexistent")

        with pytest.raises(KeyError):
            system.dashboard("nonexistent")


class TestLab14ApiIntegration:

    def test_lab14_demo_endpoint(self):
        """FastAPI route /lab14/demo must return full integration results."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab14/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["lab"] == "Lab 14: Capstone — Full Team-Owned Deployed System"

        steps = data["steps"]
        assert steps["step1_system_status"]["labs_integrated"] == 14
        assert steps["step2_pipeline_execution"]["labs_integrated"] == 14
        assert steps["step3_faculty_approval"]["status"] == "approved"
        assert steps["step4_governed_publish"]["status"] == "published"
        assert "notes_portal" in steps["step5_faculty_dashboard"]
        assert steps["step6_validation_report"]["all_passed"] is True

    def test_lab14_status_endpoint(self):
        """FastAPI route /lab14/status must return system health."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab14/status")

        assert response.status_code == 200
        data = response.json()
        assert data["labs_integrated"] == 14
