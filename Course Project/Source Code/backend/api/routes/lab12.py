"""
Lab 12: Safety & Governance — Approval, Eval, Rollback Route
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  • GET  /lab12/demo                  — End-to-end demonstration of Lab 12 governance workflow
  • POST /lab12/confidentiality-view  — Filters workspace by role (Faculty unrestricted vs Student restricted)
  • POST /lab12/approve-and-publish   — Named human faculty approval gate, metrics recording, v+1 publishing
  • POST /lab12/rollback              — 1-click rollback restoring historical version cleanly
  • GET  /lab12/history/{course_id}   — Returns complete version history and audit releases for a course
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runtime.governance_release import (
    SafetyGovernanceManager,
    RoleContext,
    VersionedRelease,
    RollbackResult,
)

router = APIRouter(prefix="/lab12", tags=["Lab 12: Safety, Access Control & Governed Rollback"])

# Shared in-memory manager instance for stateful route operations
governance_manager = SafetyGovernanceManager()


class ConfidentialityRequest(BaseModel):
    workspace: Dict[str, Any]
    user_id: int = 5
    name: str = "Alex Chen"
    role: str = "student"


class ApprovePublishRequest(BaseModel):
    draft: Dict[str, Any]
    faculty_id: int = 1
    faculty_name: str = "Dr. Vaishnavi Patel"
    human_edits: Optional[List[Dict[str, Any]]] = None


class RollbackRequest(BaseModel):
    course_id: int = 1
    target_version: int = 1
    faculty_id: int = 1
    faculty_name: str = "Dr. Vaishnavi Patel"


def _build_sample_draft_workspace() -> Dict[str, Any]:
    """Builds a realistic course workspace draft for demonstration."""
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
                "feedback": "Flawless LangGraph StateGraph implementation with robust back-edge handling.",
                "held_for_plagiarism": False,
            },
            {
                "submission_id": "sub_bob_102",
                "student_name": "Bob Miller",
                "raw_score": 75.0,
                "final_score": 65.0,
                "feedback": "Solid ReAct loop; 10 marks deducted for 1-day late submission.",
                "held_for_plagiarism": False,
            },
            {
                "submission_id": "sub_charlie_103",
                "student_name": "Charlie Brown",
                "raw_score": 0.0,
                "final_score": 0.0,
                "feedback": "Quarantined: High code similarity (0.92) detected against external repository.",
                "held_for_plagiarism": True,
            },
        ],
        "evidence_table": [
            {"claim": "StateGraph compiles", "source": "test_graph.py:L14", "grounded": True},
            {"claim": "External code matches", "source": "github.com/prior/ref.py", "grounded": True},
        ],
        "audit_trail": [
            {"step": "swarm_eval", "status": "completed", "cost_credits": 25},
            {"step": "similarity_engine", "status": "flagged_charlie", "cost_credits": 10},
        ],
    }


@router.get("/demo")
async def run_lab12_demo() -> Dict[str, Any]:
    """
    Demonstrates Lab 12 Safety & Governance:
      1. Confidentiality: Student cannot see peers' submissions or unapproved draft grades.
      2. Faculty Unrestricted View: Faculty sees all submissions, flags, and raw evaluations.
      3. Named Human Faculty Approval Gate: Applies faculty manual overrides and publishes v1.
      4. Metrics Recording: Evaluates mean, median, distribution, and quarantine rates.
      5. Second Revision: Faculty publishes v2 with revised rubric adjustments.
      6. One-Click Rollback: Faculty triggers instant 1-click restoration to v1.
      7. Hard Stop on Unauthorized Actors: Student is strictly blocked from approving or rolling back.
    """
    demo_manager = SafetyGovernanceManager()
    draft = _build_sample_draft_workspace()

    faculty_actor = RoleContext.faculty(user_id=1, name="Dr. Vaishnavi Patel")
    student_actor = RoleContext.student(user_id=5, name="Alex Chen")
    unauth_student = RoleContext.student(user_id=9, name="Intruder Student")

    # Step 1: Student view of unapproved draft
    student_draft_view = demo_manager.enforce_confidentiality(draft, student_actor)

    # Step 2: Faculty view of unapproved draft
    faculty_draft_view = demo_manager.enforce_confidentiality(draft, faculty_actor)

    # Step 3: Hard stop unauthorized approval attempt
    student_blocked = False
    try:
        demo_manager.review_and_approve(draft, unauth_student)
    except PermissionError:
        student_blocked = True

    # Step 4: Named Faculty Review and Approval (Publishing v1)
    # Faculty adds a 10-point bonus to Bob Miller for novel reflection architecture
    human_edits_v1 = [
        {
            "submission_id": "sub_bob_102",
            "new_score": 75.0,
            "reason": "Faculty bonus: Approved late waiver due to certified medical note."
        }
    ]
    release_v1 = demo_manager.review_and_approve(
        draft=draft,
        actor=faculty_actor,
        human_edits=human_edits_v1
    )

    # Step 5: Student view post-publish v1 (Alex Chen sees his approved 92.0 score, but not peers)
    student_v1_view = demo_manager.enforce_confidentiality(release_v1.workspace_snapshot, student_actor)

    # Step 6: Create and publish revision v2
    draft_v2 = _build_sample_draft_workspace()
    draft_v2["grading_results"][0]["final_score"] = 98.0  # Alex bonus
    release_v2 = demo_manager.review_and_approve(
        draft=draft_v2,
        actor=faculty_actor,
        human_edits=[
            {
                "submission_id": "sub_alex_101",
                "new_score": 98.0,
                "reason": "Faculty awarded 6 extra points for exceptional AST test coverage."
            }
        ]
    )

    # Step 7: 1-Click Rollback to v1
    rollback_result = demo_manager.rollback(course_id=1, target_version=1, actor=faculty_actor)

    return {
        "status": "success",
        "lab": "Lab 12: Safety & Governance — Approval, Eval, Rollback",
        "guiding_principle": "Agents draft and flag; a named human approves.",
        "steps": {
            "step1_student_draft_confidentiality": {
                "access_level": student_draft_view.get("access_level"),
                "visible_submissions_count": len(student_draft_view.get("submissions", [])),
                "visible_student": student_draft_view.get("submissions", [])[0]["student_name"],
                "grade_status": student_draft_view.get("grading_results", [])[0]["final_score"],
                "evidence_table_stripped": "evidence_table" not in student_draft_view,
                "audit_trail_stripped": "audit_trail" not in student_draft_view,
            },
            "step2_faculty_unrestricted_view": {
                "access_level": faculty_draft_view.get("access_level"),
                "visible_submissions_count": len(faculty_draft_view.get("submissions", [])),
                "unmasked_grades_count": len(faculty_draft_view.get("grading_results", [])),
            },
            "step3_unauthorized_student_blocked": {
                "hard_stop_enforced": student_blocked,
                "reason": "require actor.can_approve strictly raised PermissionError",
            },
            "step4_published_release_v1": {
                "release_id": release_v1.release_id,
                "version": release_v1.version,
                "approved_by": release_v1.approved_by,
                "human_edits_applied": len(release_v1.human_edits),
                "metrics": release_v1.metrics.model_dump(),
            },
            "step5_student_post_publish_view": {
                "grade_unmasked": student_v1_view.get("grading_results", [])[0]["final_score"],
                "feedback": student_v1_view.get("grading_results", [])[0]["feedback"],
                "can_see_peer_submissions": len(student_v1_view.get("submissions", [])) > 1,
            },
            "step6_published_release_v2": {
                "release_id": release_v2.release_id,
                "version": release_v2.version,
                "active_version": demo_manager.active_versions.get(1),
            },
            "step7_one_click_rollback_to_v1": {
                "target_version": rollback_result.target_version,
                "active_version_now": rollback_result.active_version,
                "restored_release_id": rollback_result.restored_release_id,
                "rolled_back_by": rollback_result.rolled_back_by,
                "alex_score_in_active_workspace": rollback_result.restored_workspace["grading_results"][0]["final_score"],
            },
        },
        "version_history_summary": {
            v: {
                "release_id": rel.release_id,
                "approved_by": rel.approved_by,
                "avg_score": rel.metrics.average_score,
                "published_at": rel.published_at,
            }
            for v, rel in demo_manager.version_history.get(1, {}).items()
        },
    }


@router.post("/confidentiality-view")
async def get_confidentiality_view(request: ConfidentialityRequest) -> Dict[str, Any]:
    """Applies role-based confidentiality rules to a workspace."""
    if request.role == "faculty":
        actor = RoleContext.faculty(user_id=request.user_id, name=request.name)
    elif request.role == "hod":
        actor = RoleContext.hod(user_id=request.user_id, name=request.name)
    else:
        actor = RoleContext.student(user_id=request.user_id, name=request.name)

    return governance_manager.enforce_confidentiality(request.workspace, actor)


@router.post("/approve-and-publish")
async def approve_and_publish(request: ApprovePublishRequest) -> Dict[str, Any]:
    """Course faculty approval gate: records metrics, publishes new version v+1."""
    faculty_actor = RoleContext.faculty(user_id=request.faculty_id, name=request.faculty_name)
    try:
        release = governance_manager.review_and_approve(
            draft=request.draft,
            actor=faculty_actor,
            human_edits=request.human_edits
        )
        return release.model_dump()
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/rollback")
async def execute_rollback(request: RollbackRequest) -> Dict[str, Any]:
    """One-click rollback: restores target version v cleanly."""
    faculty_actor = RoleContext.faculty(user_id=request.faculty_id, name=request.faculty_name)
    try:
        result = governance_manager.rollback(
            course_id=request.course_id,
            target_version=request.target_version,
            actor=faculty_actor
        )
        return result.model_dump()
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/history/{course_id}")
async def get_version_history(course_id: int) -> Dict[str, Any]:
    """Returns all published version releases and active version for a course."""
    versions = governance_manager.version_history.get(course_id, {})
    active = governance_manager.active_versions.get(course_id, None)
    return {
        "course_id": course_id,
        "active_version": active,
        "total_versions": len(versions),
        "releases": [rel.model_dump() for rel in versions.values()],
    }
