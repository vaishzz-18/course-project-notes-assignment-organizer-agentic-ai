"""
Acceptance Test Suite for Lab 3: Skill Creation — Reusable Plan & Format Skills
Verifies:
1. Two callable skills with strict Pydantic schemas (PlanSkill & FormatSkill).
2. The exact same skill works for two completely different cases:
   - Case A: Theory Course (CS301 Theory of Computation)
   - Case B: Lab Course (CS401 Agentic AI Lab)
   WITHOUT ANY CODE CHANGES.
3. Cryptographic plan fingerprinting and immutability.
4. Formatted workspace rendering with human governance gate.
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.course_skills import (
    PlanSkill,
    FormatSkill,
    PlanInputSchema,
    AssignmentSpecSchema,
    MilestoneSpecSchema,
    CriterionSchema,
    FormatInputSchema,
    LockedPlanSchema,
    FormattedDocumentSchema
)


def test_lab3_polymorphic_reusability_across_two_different_courses():
    """
    Acceptance Test: Demonstrates that PlanSkill and FormatSkill execute
    polymorphically across two totally different courses without code modifications.
    """
    plan_skill = PlanSkill()
    format_skill = FormatSkill()

    # =========================================================================
    # CASE 1: Theory Course — CS301 Theory of Computation (Mathematical Proofs)
    # =========================================================================
    theory_input = PlanInputSchema(
        course_name="Theory of Computation & Automata",
        course_code="CS301",
        course_type="theory",
        faculty_lead="Prof. Alan Turing",
        units=["Unit 1: Regular Languages & DFA", "Unit 2: Context-Free Grammars", "Unit 3: Turing Machines & Decidability"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="theory_a1",
                title="Pumping Lemma & DFA Minimization Proofs",
                unit_reference="Unit 1",
                max_marks=50.0,
                is_coding_task=False,
                rubric=[
                    CriterionSchema(name="Formal Proof Rigor", weight=25.0, description="Mathematical soundness of reduction"),
                    CriterionSchema(name="Boundary Cases", weight=25.0, description="Handling empty string and infinite loops")
                ]
            ),
            AssignmentSpecSchema(
                assignment_id="theory_a2",
                title="Turing Machine Halting Reductions",
                unit_reference="Unit 3",
                max_marks=50.0,
                is_coding_task=False,
                rubric=[
                    CriterionSchema(name="Reduction Accuracy", weight=30.0, description="Rice theorem proof application"),
                    CriterionSchema(name="Explanation Clarity", weight=20.0, description="Written argumentation")
                ]
            )
        ],
        milestones=[
            MilestoneSpecSchema(
                checkpoint_number=1,
                title="Theoretical Research Paper Review",
                deliverable="Survey of P vs NP approximation limits",
                week_deadline=12
            )
        ],
        similarity_threshold=0.80
    )

    locked_theory_plan: LockedPlanSchema = plan_skill.execute(theory_input)

    assert locked_theory_plan.is_locked
    assert locked_theory_plan.course_code == "CS301"
    assert locked_theory_plan.course_type == "theory"
    assert len(locked_theory_plan.slots) == 3 + 2 + 1  # 3 notes + 2 assignments + 1 milestone = 6 slots
    assert locked_theory_plan.plan_fingerprint.startswith("sha256:")

    # Render Theory Workspace via FormatSkill
    theory_format_input = FormatInputSchema(
        plan=locked_theory_plan,
        notes_summary=[
            {"unit": "Unit 1", "topic": "DFA Minimization", "version": 1, "is_current": True, "file_name": "dfa_notes.pdf"},
            {"unit": "Unit 2", "topic": "Chomsky Normal Form", "version": 1, "is_current": True, "file_name": "cfg_notes.pdf"}
        ],
        submissions_summary=[
            {"student_name": "Siddharth Roy", "status": "Submitted", "timing": "On Time", "similarity": 0.05, "draft_score": "48/50"}
        ],
        milestones_summary=[
            {"checkpoint": 1, "title": "Theoretical Research Paper Review", "week": 12, "health": "green"}
        ],
        template_type="markdown"
    )
    theory_doc: FormattedDocumentSchema = format_skill.execute(theory_format_input)

    assert theory_doc.course_code == "CS301"
    assert "CS301 — THEORY OF COMPUTATION & AUTOMATA" in theory_doc.content
    assert "Prof. Alan Turing" in theory_doc.content
    assert "FACULTY APPROVAL & GOVERNANCE GATE" in theory_doc.content

    print(f"\n[PASS] Case 1 (Theory Course): Locked Plan ID={locked_theory_plan.plan_id}, Slots={len(locked_theory_plan.slots)}, Rendered Doc ID={theory_doc.document_id}")

    # =========================================================================
    # CASE 2: Lab Course — CS401 Agentic AI Lab (Software Engineering & Agents)
    # =========================================================================
    lab_input = PlanInputSchema(
        course_name="Agentic AI & Autonomous Systems Lab",
        course_code="CS401",
        course_type="lab",
        faculty_lead="Dr. Vaishnavi Patel",
        units=["Unit 1: ReAct Agents", "Unit 2: MCP Servers", "Unit 3: LangGraph Pipelines", "Unit 4: Swarms"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="lab_a1",
                title="Build a ReAct Agent with Tool Calling",
                unit_reference="Unit 1",
                max_marks=100.0,
                is_coding_task=True,
                rubric=[
                    CriterionSchema(name="Tool Invocation", weight=40.0),
                    CriterionSchema(name="Reasoning Loop", weight=30.0),
                    CriterionSchema(name="Resilience", weight=30.0)
                ]
            )
        ],
        milestones=[
            MilestoneSpecSchema(checkpoint_number=1, title="Proposal", deliverable="Design Doc", week_deadline=4),
            MilestoneSpecSchema(checkpoint_number=2, title="Mid-term Prototype", deliverable="GitHub Repo", week_deadline=8),
            MilestoneSpecSchema(checkpoint_number=3, title="Final Swarm Demo", deliverable="Dockerized Service", week_deadline=14)
        ],
        similarity_threshold=0.75
    )

    locked_lab_plan: LockedPlanSchema = plan_skill.execute(lab_input)

    assert locked_lab_plan.is_locked
    assert locked_lab_plan.course_code == "CS401"
    assert locked_lab_plan.course_type == "lab"
    assert len(locked_lab_plan.slots) == 4 + 1 + 3  # 4 notes + 1 assignment + 3 milestones = 8 slots
    assert locked_lab_plan.plan_fingerprint != locked_theory_plan.plan_fingerprint

    # Render Lab Workspace via FormatSkill
    lab_format_input = FormatInputSchema(
        plan=locked_lab_plan,
        notes_summary=[
            {"unit": "Unit 1", "topic": "Cognitive Loops", "version": 2, "is_current": True, "file_name": "unit1_v2.txt"}
        ],
        submissions_summary=[
            {"student_name": "Alex Chen", "status": "Submitted", "timing": "On Time", "similarity": 0.12, "draft_score": "95/100"},
            {"student_name": "David Kim", "status": "Submitted", "timing": "On Time", "similarity": 0.96, "draft_score": "0/100 (Flagged)"}
        ],
        milestones_summary=[
            {"checkpoint": 1, "title": "Proposal", "week": 4, "health": "green"},
            {"checkpoint": 2, "title": "Mid-term Prototype", "week": 8, "health": "amber"}
        ],
        template_type="markdown"
    )
    lab_doc: FormattedDocumentSchema = format_skill.execute(lab_format_input)

    assert lab_doc.course_code == "CS401"
    assert "CS401 — AGENTIC AI & AUTONOMOUS SYSTEMS LAB" in lab_doc.content
    assert "Dr. Vaishnavi Patel" in lab_doc.content
    assert "⚠ **HIGH (96%)**" in lab_doc.content  # Verifies high similarity formatting

    print(f"\n[PASS] Case 2 (Lab Course): Locked Plan ID={locked_lab_plan.plan_id}, Slots={len(locked_lab_plan.slots)}, Rendered Doc ID={lab_doc.document_id}")
    print("\nACCEPTANCE CRITERIA VERIFIED: Identical skills handled 2 distinct courses with zero code changes!")


if __name__ == "__main__":
    test_lab3_polymorphic_reusability_across_two_different_courses()
    print("\nALL LAB 3 ACCEPTANCE TESTS PASSED!")
