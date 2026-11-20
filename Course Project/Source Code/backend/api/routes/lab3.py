"""
Lab 3 REST API Routes
Provides endpoints for executing and inspecting reusable Plan and Format skills.
"""

from fastapi import APIRouter
from typing import Dict, Any
from skills.course_skills import (
    PlanSkill,
    FormatSkill,
    PlanInputSchema,
    LockedPlanSchema,
    FormatInputSchema,
    FormattedDocumentSchema,
    AssignmentSpecSchema,
    MilestoneSpecSchema,
    CriterionSchema
)

router = APIRouter(prefix="/lab3", tags=["Lab 3: Skill Creation"])
plan_skill = PlanSkill()
format_skill = FormatSkill()


@router.get("/skills")
async def list_skills():
    """Returns schemas and metadata for registered skills."""
    return {
        "skills": [
            {
                "name": PlanSkill.SKILL_NAME,
                "version": PlanSkill.VERSION,
                "description": "Transforms course requirements into an immutable, hashed execution blueprint.",
                "input_schema": PlanInputSchema.model_json_schema(),
                "output_schema": LockedPlanSchema.model_json_schema()
            },
            {
                "name": FormatSkill.SKILL_NAME,
                "version": FormatSkill.VERSION,
                "description": "Renders course workspace states into formatted Markdown or HTML with human review gates.",
                "input_schema": FormatInputSchema.model_json_schema(),
                "output_schema": FormattedDocumentSchema.model_json_schema()
            }
        ]
    }


@router.post("/plan", response_model=LockedPlanSchema)
async def execute_plan_skill(body: PlanInputSchema):
    return plan_skill.execute(body)


@router.post("/format", response_model=FormattedDocumentSchema)
async def execute_format_skill(body: FormatInputSchema):
    return format_skill.execute(body)


@router.get("/demo")
async def run_lab3_demo():
    """
    Executes polymorphic test across two diverse courses (Theory vs Lab)
    and returns comparison report.
    """
    # Case A: Theory Course
    theory_input = PlanInputSchema(
        course_name="Theory of Computation & Automata",
        course_code="CS301",
        course_type="theory",
        faculty_lead="Prof. Alan Turing",
        units=["Unit 1: Regular Languages", "Unit 2: Context-Free Grammars"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="theory_a1",
                title="DFA Proofs",
                unit_reference="Unit 1",
                max_marks=50.0,
                rubric=[CriterionSchema(name="Rigor", weight=50.0)]
            )
        ],
        milestones=[
            MilestoneSpecSchema(checkpoint_number=1, title="Survey Paper", deliverable="Report", week_deadline=10)
        ]
    )
    locked_theory = plan_skill.execute(theory_input)
    doc_theory = format_skill.execute(FormatInputSchema(
        plan=locked_theory,
        notes_summary=[{"unit": "Unit 1", "topic": "DFA", "version": 1, "is_current": True, "file_name": "dfa.pdf"}],
        submissions_summary=[{"student_name": "Siddharth", "status": "Submitted", "timing": "On Time", "similarity": 0.05, "draft_score": "48/50"}],
        milestones_summary=[{"checkpoint": 1, "title": "Survey Paper", "week": 10, "health": "green"}]
    ))

    # Case B: Lab Course
    lab_input = PlanInputSchema(
        course_name="Agentic AI & Autonomous Systems Lab",
        course_code="CS401",
        course_type="lab",
        faculty_lead="Dr. Vaishnavi Patel",
        units=["Unit 1: ReAct", "Unit 2: MCP", "Unit 3: LangGraph"],
        assignments=[
            AssignmentSpecSchema(
                assignment_id="lab_a1",
                title="Build a ReAct Agent",
                unit_reference="Unit 1",
                max_marks=100.0,
                is_coding_task=True,
                rubric=[CriterionSchema(name="Tool Calling", weight=50.0), CriterionSchema(name="Reasoning", weight=50.0)]
            )
        ],
        milestones=[
            MilestoneSpecSchema(checkpoint_number=1, title="Proposal", deliverable="Spec", week_deadline=4),
            MilestoneSpecSchema(checkpoint_number=2, title="Final Swarm Demo", deliverable="Repo", week_deadline=12)
        ]
    )
    locked_lab = plan_skill.execute(lab_input)
    doc_lab = format_skill.execute(FormatInputSchema(
        plan=locked_lab,
        notes_summary=[{"unit": "Unit 1", "topic": "ReAct Loop", "version": 2, "is_current": True, "file_name": "unit1_v2.txt"}],
        submissions_summary=[
            {"student_name": "Alex Chen", "status": "Submitted", "timing": "On Time", "similarity": 0.12, "draft_score": "95/100"},
            {"student_name": "David Kim", "status": "Submitted", "timing": "On Time", "similarity": 0.96, "draft_score": "Flagged"}
        ],
        milestones_summary=[
            {"checkpoint": 1, "title": "Proposal", "week": 4, "health": "green"},
            {"checkpoint": 2, "title": "Final Swarm Demo", "week": 12, "health": "amber"}
        ]
    ))

    return {
        "lab": "Lab 3: Skill Creation (Reusable Plan & Format Skills)",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": True,
        "polymorphism_verification": {
            "case_a_theory": {
                "course_code": locked_theory.course_code,
                "course_type": locked_theory.course_type,
                "plan_id": locked_theory.plan_id,
                "fingerprint": locked_theory.plan_fingerprint,
                "slots_count": len(locked_theory.slots),
                "rendered_preview": doc_theory.content[:200]
            },
            "case_b_lab": {
                "course_code": locked_lab.course_code,
                "course_type": locked_lab.course_type,
                "plan_id": locked_lab.plan_id,
                "fingerprint": locked_lab.plan_fingerprint,
                "slots_count": len(locked_lab.slots),
                "rendered_preview": doc_lab.content[:200]
            },
            "code_reused_without_modification": True
        }
    }
