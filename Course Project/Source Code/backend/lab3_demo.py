"""
Interactive Demonstration CLI for Lab 3: Skill Creation (Reusable Plan & Format Skills)
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Reusable skill abstraction (PlanSkill & FormatSkill)
2. Case A: Theory Course (CS301 Theory of Computation)
3. Case B: Lab Course (CS401 Agentic AI Lab)
4. Proof of zero code modifications between distinct domain variants.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from skills.course_skills import (
    PlanSkill,
    FormatSkill,
    PlanInputSchema,
    AssignmentSpecSchema,
    MilestoneSpecSchema,
    CriterionSchema,
    FormatInputSchema
)


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab3_demonstration():
    plan_skill = PlanSkill()
    format_skill = FormatSkill()

    print_banner("LAB 3: SKILL CREATION (REUSABLE PLAN & FORMAT SKILLS)")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Goal: Package repeatable capability as reusable, schema-typed skills.")
    print("Acceptance Rule: The same skill works for two different cases without code changes.\n")

    # -------------------------------------------------------------
    # CASE 1: Theory Course
    # -------------------------------------------------------------
    print_banner("CASE 1: Theory Course (CS301 Theory of Computation)")
    theory_input = PlanInputSchema(
        course_name="Theory of Computation & Automata",
        course_code="CS301",
        course_type="theory",
        faculty_lead="Prof. Alan Turing",
        units=["Unit 1: Regular Languages & DFA", "Unit 2: Context-Free Grammars", "Unit 3: Turing Machines & Decidability"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="a1",
                title="Pumping Lemma & DFA Reduction Proofs",
                unit_reference="Unit 1",
                max_marks=50.0,
                rubric=[
                    CriterionSchema(name="Formal Proof Rigor", weight=25.0),
                    CriterionSchema(name="Boundary Cases", weight=25.0)
                ]
            )
        ],
        milestones=[
            MilestoneSpecSchema(checkpoint_number=1, title="P vs NP Survey Paper", deliverable="Survey Report", week_deadline=12)
        ]
    )

    print("Invoking PlanSkill.execute(theory_input)...")
    theory_plan = plan_skill.execute(theory_input)
    print(f"  Plan ID: {theory_plan.plan_id}")
    print(f"  Fingerprint: {theory_plan.plan_fingerprint}")
    print(f"  Slots Count: {len(theory_plan.slots)}")

    print("\nInvoking FormatSkill.execute(theory_plan)...")
    theory_doc = format_skill.execute(FormatInputSchema(
        plan=theory_plan,
        notes_summary=[{"unit": "Unit 1", "topic": "DFA", "version": 1, "is_current": True, "file_name": "dfa.pdf"}],
        submissions_summary=[{"student_name": "Siddharth", "status": "Submitted", "timing": "On Time", "similarity": 0.04, "draft_score": "47/50"}],
        milestones_summary=[{"checkpoint": 1, "title": "P vs NP Survey", "week": 12, "health": "green"}]
    ))
    print(f"  Rendered Document ID: {theory_doc.document_id}")
    print(f"  Document Preview (First 5 lines):")
    for line in theory_doc.content.split("\n")[:5]:
        print(f"    {line}")

    # -------------------------------------------------------------
    # CASE 2: Lab Course
    # -------------------------------------------------------------
    print_banner("CASE 2: Lab Course (CS401 Agentic AI Lab)")
    lab_input = PlanInputSchema(
        course_name="Agentic AI & Autonomous Systems Lab",
        course_code="CS401",
        course_type="lab",
        faculty_lead="Dr. Vaishnavi Patel",
        units=["Unit 1: ReAct Agents", "Unit 2: MCP Tools", "Unit 3: LangGraph Pipelines", "Unit 4: Swarms"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="a1",
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
            MilestoneSpecSchema(checkpoint_number=1, title="Architecture Proposal", deliverable="Design Doc", week_deadline=4),
            MilestoneSpecSchema(checkpoint_number=2, title="Mid-term Prototype", deliverable="GitHub Repo", week_deadline=8),
            MilestoneSpecSchema(checkpoint_number=3, title="Final Swarm Demo", deliverable="Dockerized Service", week_deadline=14)
        ]
    )

    print("Invoking PlanSkill.execute(lab_input) [EXACT SAME CODE]...")
    lab_plan = plan_skill.execute(lab_input)
    print(f"  Plan ID: {lab_plan.plan_id}")
    print(f"  Fingerprint: {lab_plan.plan_fingerprint}")
    print(f"  Slots Count: {len(lab_plan.slots)}")

    print("\nInvoking FormatSkill.execute(lab_plan) [EXACT SAME CODE]...")
    lab_doc = format_skill.execute(FormatInputSchema(
        plan=lab_plan,
        notes_summary=[{"unit": "Unit 1", "topic": "Cognitive Loops", "version": 2, "is_current": True, "file_name": "unit1_v2.txt"}],
        submissions_summary=[
            {"student_name": "Alex Chen", "status": "Submitted", "timing": "On Time", "similarity": 0.12, "draft_score": "95/100"},
            {"student_name": "David Kim", "status": "Submitted", "timing": "On Time", "similarity": 0.96, "draft_score": "Flagged"}
        ],
        milestones_summary=[
            {"checkpoint": 1, "title": "Architecture Proposal", "week": 4, "health": "green"},
            {"checkpoint": 2, "title": "Mid-term Prototype", "week": 8, "health": "amber"}
        ]
    ))
    print(f"  Rendered Document ID: {lab_doc.document_id}")
    print(f"  Document Preview (First 5 lines):")
    for line in lab_doc.content.split("\n")[:5]:
        print(f"    {line}")

    print_banner("LAB 3 DEMONSTRATION COMPLETE: ZERO CODE CHANGES ACROSS DIVERSE CASES")


if __name__ == "__main__":
    run_lab3_demonstration()
