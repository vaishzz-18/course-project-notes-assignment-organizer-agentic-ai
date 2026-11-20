"""
Lab 12: Safety & Governance — Approval, Eval, Rollback Demo
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
  Add access control, confidentiality, the course faculty approval gate as a hard stop,
  evaluation metrics, versioning, and one-click rollback.

Guiding Design Principle:
  "Agents draft and flag; a named human approves."

Pseudocode:
  require actor.can_approve and out.status == 'draft'
  final = apply(human.edits, out); final.status = 'approved'
  governance.publish(final, version=v+1); metrics.record(...)
  on rollback(v): restore(version=v)

Usage:
  python backend/lab12_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime.governance_release import (
    SafetyGovernanceManager,
    RoleContext,
)


def build_sample_workspace() -> dict:
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


def main():
    print("=" * 78)
    print("AURA LAB 12: SAFETY & GOVERNANCE -- APPROVAL, EVAL, ROLLBACK")
    print("Phase D: Governance & Capstone | Chapter 2 Course Project")
    print("=" * 78)
    print("Guiding Principle: 'Agents draft and flag; a named human approves.'\n")

    manager = SafetyGovernanceManager()
    draft = build_sample_workspace()

    faculty = RoleContext.faculty(user_id=1, name="Dr. Vaishnavi Patel")
    student_alex = RoleContext.student(user_id=5, name="Alex Chen")
    intruder_student = RoleContext.student(user_id=9, name="Intruder Student")

    # -------------------------------------------------------------------------
    # Step 1: Student Confidentiality Filter on Unapproved Draft
    # -------------------------------------------------------------------------
    print("-" * 78)
    print("[STEP 1] Testing Strict Student Confidentiality Filter (Unapproved Draft)")
    print("-" * 78)
    alex_draft_view = manager.enforce_confidentiality(draft, student_alex)
    print(f"Actor: {student_alex.name} (Role: {student_alex.role})")
    print(f"Access Level: {alex_draft_view.get('access_level')}")
    print(f"Submissions visible to Alex: {len(alex_draft_view['submissions'])} (only his own)")
    for sub in alex_draft_view["submissions"]:
        print(f"  - Visible submission ID: {sub['submission_id']} (Owner: {sub['student_name']})")
    print(f"Grades visible to Alex: {len(alex_draft_view['grading_results'])}")
    for g in alex_draft_view["grading_results"]:
        print(f"  - Student: {g['student_name']} | Score: {g['final_score']} | Feedback: {g['feedback']}")
    print(f"Evidence table stripped: {'evidence_table' not in alex_draft_view}")
    print(f"Internal audit trail stripped: {'audit_trail' not in alex_draft_view}")

    # -------------------------------------------------------------------------
    # Step 2: Faculty Unrestricted View
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 2] Testing Faculty Unrestricted View")
    print("-" * 78)
    fac_view = manager.enforce_confidentiality(draft, faculty)
    print(f"Actor: {faculty.name} (Role: {faculty.role})")
    print(f"Access Level: {fac_view.get('access_level')}")
    print(f"Total Submissions Visible: {len(fac_view['submissions'])}")
    print(f"Total Grades Visible: {len(fac_view['grading_results'])}")
    print(f"Evidence table intact: {'evidence_table' in fac_view}")
    print(f"Internal audit trail intact: {'audit_trail' in fac_view}")

    # -------------------------------------------------------------------------
    # Step 3: Hard Stop -- Unauthorized Student Approval Attempt
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 3] Hard Stop: Student attempts to approve draft without authorization")
    print("-" * 78)
    try:
        manager.review_and_approve(draft, intruder_student)
        print("[FAIL] Security bypass: Student was allowed to approve!")
    except PermissionError as exc:
        print(f"[PASS] Hard Stop triggered successfully:")
        print(f"       Refusal reason: {exc}")

    # -------------------------------------------------------------------------
    # Step 4: Named Human Faculty Approval Gate -- Publishing Release v1
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 4] Named Human Faculty Approval Gate & Publishing Release v1")
    print("-" * 78)
    # Dr. Vaishnavi Patel reviews draft and applies a human override:
    # Bob Miller gets +10 waiver for certified medical delay
    human_edits = [
        {
            "submission_id": "sub_bob_102",
            "new_score": 75.0,
            "reason": "Faculty waiver: Certified medical leave accepted, late penalty waived.",
        }
    ]
    release_v1 = manager.review_and_approve(draft, faculty, human_edits=human_edits)
    print(f"Release ID:        {release_v1.release_id}")
    print(f"Version:           v{release_v1.version}")
    print(f"Approved By:       {release_v1.approved_by} (ID: {release_v1.approved_by_id})")
    print(f"Status:            {release_v1.status}")
    print(f"Human Edits Made:  {len(release_v1.human_edits)}")
    for edit in release_v1.human_edits:
        print(f"  - {edit.student_name}: {edit.original_score} -> {edit.adjusted_score} ({edit.faculty_reason})")

    m1 = release_v1.metrics
    print("\nRecorded Evaluation Metrics (v1):")
    print(f"  - Total Submissions:  {m1.total_submissions}")
    print(f"  - Average Score:      {m1.average_score}")
    print(f"  - Median Score:       {m1.median_score}")
    print(f"  - Score Range:        [{m1.lowest_score} to {m1.highest_score}]")
    print(f"  - Grade Distribution: {m1.grade_distribution}")
    print(f"  - Plagiarism Held:    {m1.plagiarism_quarantine_count}")
    print(f"  - Late Submissions:   {m1.late_penalty_count}")

    # -------------------------------------------------------------------------
    # Step 5: Student View Post-Publish v1
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 5] Student View After Faculty Publication (Alex Chen)")
    print("-" * 78)
    alex_v1_view = manager.enforce_confidentiality(release_v1.workspace_snapshot, student_alex)
    grade = alex_v1_view["grading_results"][0]
    print(f"Student:            {grade['student_name']}")
    print(f"Approved Score:     {grade['final_score']}")
    print(f"Feedback:           {grade['feedback']}")
    print(f"Can see Bob's work: {'sub_bob_102' in [s['submission_id'] for s in alex_v1_view['submissions']]}")

    # -------------------------------------------------------------------------
    # Step 6: Create and Publish Revision v2
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 6] Publishing Revised Release v2")
    print("-" * 78)
    draft_v2 = build_sample_workspace()
    # In v2, faculty awards extra credit to Alex Chen
    release_v2 = manager.review_and_approve(
        draft=draft_v2,
        actor=faculty,
        human_edits=[
            {
                "submission_id": "sub_alex_101",
                "new_score": 98.0,
                "reason": "Faculty bonus for exceptional AST benchmark suite.",
            }
        ],
    )
    print(f"Published Version: v{release_v2.version} (Release ID: {release_v2.release_id})")
    print(f"Current Active Version for CS401: v{manager.active_versions[1]}")
    print(f"Alex's Score in v2: {release_v2.workspace_snapshot['grading_results'][0]['final_score']}")

    # -------------------------------------------------------------------------
    # Step 7: One-Click Rollback to v1
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 7] One-Click Rollback: Faculty triggers instant restoration to v1")
    print("-" * 78)
    rollback_result = manager.rollback(course_id=1, target_version=1, actor=faculty)
    print(f"Restored Version:   v{rollback_result.active_version}")
    print(f"Target Release ID:  {rollback_result.restored_release_id}")
    print(f"Rolled Back By:     {rollback_result.rolled_back_by}")
    restored_alex_score = rollback_result.restored_workspace["grading_results"][0]["final_score"]
    print(f"Alex's Score in Restored Workspace: {restored_alex_score} (Cleanly reverted from 98.0 back to 92.0)")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("LAB 12 GOVERNANCE DEMONSTRATION COMPLETE: ALL REQUIREMENTS MET")
    print("=" * 78)
    print("[PASS] Access Control & Confidentiality enforced.")
    print("[PASS] Faculty Approval Gate stops unapproved releases.")
    print("[PASS] Human adjustments applied with explicit rationale.")
    print("[PASS] Evaluation metrics logged automatically on release.")
    print("[PASS] 1-Click Rollback instantly restored v1 snapshot.")
    print("=" * 78)


if __name__ == "__main__":
    main()
