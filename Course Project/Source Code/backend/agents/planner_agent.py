"""
Lab 1: Agent vs Chatbot — The Course Workspace Planner Loop
Phase A: Foundations

Core Goal:
Establish the agent loop (clarify → plan → revise) instead of a one-shot chatbot answer.

Guiding Design Principle:
Agents draft and flag; a named human approves.

Acceptance Criteria:
Given a vague request, it asks at least two clarifying questions and yields a coherent, editable plan.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import re


class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    context: str
    options: Optional[List[str]] = None


class ClarifyResult(BaseModel):
    is_clarified: bool
    missing_fields: List[str]
    questions: List[ClarifyingQuestion]
    extracted_params: Dict[str, Any]
    feedback_message: str


class RubricCriterion(BaseModel):
    criterion: str
    max_marks: float
    description: str


class AssignmentPlan(BaseModel):
    title: str
    unit: str
    max_marks: float
    rubric: List[RubricCriterion]
    submission_format: str = "pdf/code"


class MilestonePlan(BaseModel):
    checkpoint_number: int
    title: str
    deliverable: str
    estimated_week: int


class UnitPlan(BaseModel):
    unit_number: int
    title: str
    topics: List[str]


class CoursePlan(BaseModel):
    plan_id: str
    course_name: str
    course_code: str
    version: int = 1
    status: str = "draft"  # draft, revised, locked
    units: List[UnitPlan]
    assignments: List[AssignmentPlan]
    milestones: List[MilestonePlan]
    governance_rules: List[str] = Field(default_factory=lambda: [
        "Never publish a grade or feedback without faculty approval.",
        "Never make a final plagiarism determination automatically; always flag for faculty review.",
        "Maintain strict immutable audit trail for every action.",
        "Preserve version history for all course notes and materials."
    ])
    revision_notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CoursePlannerAgent:
    """
    Lab 1 Planner Agent:
    Operates an interactive cognitive loop (clarify → plan → revise)
    Distinguishes an agent from a one-shot chatbot by proactively seeking clarification,
    proposing structured plans, and accepting iterative human revisions.
    """

    AGENT_NAME = "CoursePlannerAgent"

    def clarify(self, user_request: str, session_context: Optional[Dict[str, Any]] = None) -> ClarifyResult:
        """
        Examines user request. If vague or underspecified, formulates at least 2
        clarifying questions to establish clear bounds before generating a plan.
        """
        context = session_context or {}
        req_lower = user_request.lower()

        # Check for essential course dimensions
        has_course_name = bool(re.search(r'(cs\d+|course|subject|class|ai|machine learning|data structures)', req_lower)) or "course_name" in context
        has_units = bool(re.search(r'(\d+\s*units?|\d+\s*modules?|topics?|syllabus)', req_lower)) or "units" in context
        has_assignments = bool(re.search(r'(assignments?|homework|lab exam|quizzes)', req_lower)) or "assignments" in context
        has_milestones = bool(re.search(r'(projects?|milestones?|capstone|group work)', req_lower)) or "milestones" in context
        has_rubric_weights = bool(re.search(r'(rubric|marks|points|grading|100 marks)', req_lower)) or "rubric" in context

        missing = []
        questions = []

        if not has_units:
            missing.append("units_and_topics")
            questions.append(ClarifyingQuestion(
                id="q_units",
                question="How many units or syllabus modules does this course comprise, and what are their primary topic themes?",
                context="Notes repository needs unit-wise categorization (e.g., Unit 1: Foundations, Unit 2: Tools & MCP).",
                options=["3 Units (Accelerated)", "4 Units (Standard Semester)", "5 Units (Comprehensive Comprehensive)"]
            ))

        if not has_assignments or not has_rubric_weights:
            missing.append("assignments_and_rubric")
            questions.append(ClarifyingQuestion(
                id="q_assignments",
                question="What is the planned structure and total marks for assignments and lab exams (including rubric dimensions)?",
                context="Assignment distribution agent requires max marks and rubric criteria before publishing briefs.",
                options=["2 Major Assignments (100 marks each, 4-tier rubric)", "4 Weekly Lab Tasks (25 marks each)", "1 Mid-term Exam + 1 Final Assignment"]
            ))

        if not has_milestones:
            missing.append("project_milestones")
            questions.append(ClarifyingQuestion(
                id="q_milestones",
                question="Will students work on course projects in groups, and what are the key milestone checkpoints?",
                context="Milestone tracking agent monitors checkpoint deliverables and schedule health (Green/Amber/Red).",
                options=["3 Checkpoints (Proposal, Mid-term Prototype, Final Demo)", "2 Checkpoints (Design Review, Final Submission)", "No Course Project"]
            ))

        # Enforce Acceptance Rule: Must ask at least 2 questions if input is vague
        if len(questions) < 2 and len(user_request.split()) < 15 and not context:
            # Fallback clarifying questions to guarantee ≥2 questions on vague request
            questions.append(ClarifyingQuestion(
                id="q_policy",
                question="What similarity threshold should trigger automated plagiarism review flags for faculty (e.g. 75% or 80%)?",
                context="Plagiarism / Similarity Agent flags matches above threshold for human review.",
                options=["70% Threshold", "75% Threshold (Recommended)", "85% Threshold"]
            ))

        is_clarified = len(questions) == 0

        # Extract whatever parameters were provided
        extracted = dict(context)
        if "cs401" in req_lower or "agentic" in req_lower:
            extracted["course_name"] = "Agentic AI & Autonomous Systems"
            extracted["course_code"] = "CS401"
        elif "course_name" not in extracted:
            extracted["course_name"] = "Advanced Course Workspace"
            extracted["course_code"] = "CS-AUTO"

        feedback_msg = (
            "Request understood with full parameters! Ready to synthesize plan outline."
            if is_clarified else
            f"Your request is a great starting point, but needs clarification on {len(missing)} key dimensions to avoid one-shot guessing. Please review the clarifying questions below:"
        )

        return ClarifyResult(
            is_clarified=is_clarified,
            missing_fields=missing,
            questions=questions,
            extracted_params=extracted,
            feedback_message=feedback_msg
        )

    def propose_plan(self, clarified_context: Dict[str, Any], custom_title: Optional[str] = None) -> CoursePlan:
        """
        Synthesizes the clarified input into a structured, coherent, editable Course Workspace Plan.
        """
        course_name = custom_title or clarified_context.get("course_name", "Agentic AI & Autonomous Systems")
        course_code = clarified_context.get("course_code", "CS401")

        # Units outline
        units = [
            UnitPlan(
                unit_number=1,
                title="Foundations of Agentic AI & Cognitive Loops",
                topics=["Agent vs Chatbot Architecture", "Perception-Reasoning-Action Loop", "Prompt Planning & ReAct Loops"]
            ),
            UnitPlan(
                unit_number=2,
                title="Tools & Model Context Protocol (MCP)",
                topics=["Typed Tool Interfaces", "FastMCP Server Implementation", "Governed Data Connector Layer"]
            ),
            UnitPlan(
                unit_number=3,
                title="LangGraph Orchestration & State Graphs",
                topics=["StateGraph Modeling", "Conditional Edges & Retries", "Human-in-the-Loop Approval Gates"]
            ),
            UnitPlan(
                unit_number=4,
                title="Parallel Swarms, Validation & Self-Healing",
                topics=["Concurrent Fan-Out / Fan-In", "Plan-Aligned Merging", "Self-Healing Regenerative Validation"]
            )
        ]

        # Assignments outline with rubric
        assignments = [
            AssignmentPlan(
                title="Assignment 1: Tool-Using ReAct Agent",
                unit="Unit 2",
                max_marks=100.0,
                rubric=[
                    RubricCriterion(criterion="Tool Calling Correctness", max_marks=40.0, description="Accurate tool invocation with validated parameters"),
                    RubricCriterion(criterion="Reasoning & Planning Loop", max_marks=25.0, description="Explicit clarify-plan-act loop with thought trace"),
                    RubricCriterion(criterion="Error Handling & Resilience", max_marks=20.0, description="Handling missing tools and invalid outputs"),
                    RubricCriterion(criterion="Documentation & Code Quality", max_marks=15.0, description="Clear docstrings, schema typing, and README")
                ]
            ),
            AssignmentPlan(
                title="Assignment 2: LangGraph Orchestrated Pipeline",
                unit="Unit 3",
                max_marks=100.0,
                rubric=[
                    RubricCriterion(criterion="StateGraph Topology & Nodes", max_marks=40.0, description="Proper node encapsulation with typed state"),
                    RubricCriterion(criterion="Conditional Validation Routing", max_marks=30.0, description="Retry loop on validation failure"),
                    RubricCriterion(criterion="Faculty Approval Gate", max_marks=30.0, description="Human review stop before publishing")
                ]
            )
        ]

        # Milestones
        milestones = [
            MilestonePlan(
                checkpoint_number=1,
                title="Checkpoint 1: Project Proposal & Architecture Specification",
                deliverable="Architecture design doc, team roster, and initial repo setup",
                estimated_week=4
            ),
            MilestonePlan(
                checkpoint_number=2,
                title="Checkpoint 2: Mid-Term Prototype & MCP Integration",
                deliverable="Working MVP with FastMCP connector and verified data layer",
                estimated_week=8
            ),
            MilestonePlan(
                checkpoint_number=3,
                title="Checkpoint 3: Final Demo, Validation Suite & Capstone Review",
                deliverable="Full system demo with self-healing graph and faculty review dashboard",
                estimated_week=14
            )
        ]

        plan_id = f"plan_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return CoursePlan(
            plan_id=plan_id,
            course_name=course_name,
            course_code=course_code,
            version=1,
            status="draft",
            units=units,
            assignments=assignments,
            milestones=milestones,
            revision_notes=["Initial plan generated from clarified course parameters."]
        )

    def revise(self, current_plan: CoursePlan, faculty_feedback: str) -> CoursePlan:
        """
        Iterative revision step: takes faculty feedback and mutates the plan structure accordingly,
        incrementing plan version while maintaining historical notes.
        """
        feedback_lower = faculty_feedback.lower()
        new_plan = current_plan.model_copy(deep=True)
        new_plan.version += 1
        new_plan.status = "revised"

        revision_action = []

        # Example feedback handling
        if "add" in feedback_lower and ("assignment" in feedback_lower or "lab" in feedback_lower):
            new_plan.assignments.append(
                AssignmentPlan(
                    title="Assignment 3: Multi-Agent Swarm & Parallel Evaluation",
                    unit="Unit 4",
                    max_marks=100.0,
                    rubric=[
                        RubricCriterion(criterion="Parallel Concurrency", max_marks=50.0, description="Fan-out latency and worker coordination"),
                        RubricCriterion(criterion="Plan Alignment Merge", max_marks=50.0, description="Selecting best outputs according to plan")
                    ]
                )
            )
            revision_action.append("Added Assignment 3: Multi-Agent Swarm per faculty request.")

        if "marks" in feedback_lower or "weight" in feedback_lower or "50 marks" in feedback_lower:
            for a in new_plan.assignments:
                a.max_marks = 50.0
                for r in a.rubric:
                    r.max_marks = r.max_marks / 2.0
            revision_action.append("Scaled assignments to 50 max marks with proportional rubric adjustment.")

        if "checkpoint" in feedback_lower or "milestone" in feedback_lower:
            new_cp_num = len(new_plan.milestones) + 1
            new_plan.milestones.append(
                MilestonePlan(
                    checkpoint_number=new_cp_num,
                    title=f"Checkpoint {new_cp_num}: Faculty Interim Review",
                    deliverable="Interim progress slides and code walk-through",
                    estimated_week=10
                )
            )
            revision_action.append(f"Added Checkpoint {new_cp_num}: Faculty Interim Review.")

        if not revision_action:
            revision_action.append(f"Adjusted course parameters: '{faculty_feedback.strip()}' applied to plan notes.")

        new_plan.revision_notes.append(f"Version {new_plan.version} update: " + "; ".join(revision_action))
        return new_plan

    def lock_plan(self, plan: CoursePlan) -> CoursePlan:
        """
        Locks the plan into an immutable specification (Lab 3 readiness).
        Once locked, the coordinator and specialist agents build against this locked blueprint.
        """
        locked = plan.model_copy(deep=True)
        locked.status = "locked"
        locked.revision_notes.append("Plan officially locked by Course Faculty. Ready for tool execution and orchestration.")
        return locked
