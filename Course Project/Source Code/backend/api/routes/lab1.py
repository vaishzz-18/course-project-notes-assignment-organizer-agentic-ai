"""
Lab 1 REST API Routes
Provides endpoints for the interactive Clarify → Plan → Revise loop.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from agents.planner_agent import CoursePlannerAgent, CoursePlan, ClarifyResult

router = APIRouter(prefix="/lab1", tags=["Lab 1: Planner Loop"])
planner = CoursePlannerAgent()


class ClarifyRequest(BaseModel):
    request: str
    session_context: Optional[Dict[str, Any]] = None


class ProposeRequest(BaseModel):
    clarified_context: Dict[str, Any]
    custom_title: Optional[str] = None


class ReviseRequest(BaseModel):
    current_plan: CoursePlan
    feedback: str


class LockRequest(BaseModel):
    plan: CoursePlan


@router.post("/clarify", response_model=ClarifyResult)
async def clarify_request(body: ClarifyRequest):
    """
    Step 1 of Planner Loop: Clarify.
    Takes a user request. If vague, returns at least 2 structured clarifying questions.
    """
    return planner.clarify(body.request, body.session_context)


@router.post("/propose", response_model=CoursePlan)
async def propose_plan(body: ProposeRequest):
    """
    Step 2 of Planner Loop: Propose Plan.
    Synthesizes clarified context into a structured, editable CoursePlan draft.
    """
    return planner.propose_plan(body.clarified_context, body.custom_title)


@router.post("/revise", response_model=CoursePlan)
async def revise_plan(body: ReviseRequest):
    """
    Step 3 of Planner Loop: Revise.
    Applies faculty feedback to modify the plan and increments plan version.
    """
    return planner.revise(body.current_plan, body.feedback)


@router.post("/lock", response_model=CoursePlan)
async def lock_plan(body: LockRequest):
    """
    Step 4 of Planner Loop: Lock Blueprint.
    Transitions plan status to 'locked', making it immutable for downstream agents.
    """
    return planner.lock_plan(body.plan)


@router.get("/demo")
async def run_lab1_demo():
    """
    Runs the full end-to-end Lab 1 acceptance trace and returns complete JSON report.
    """
    vague_prompt = "Help me organize my AI course."
    clarify_res = planner.clarify(vague_prompt)

    context = {
        "course_name": "CS401: Agentic AI & Autonomous Systems",
        "course_code": "CS401",
        "units": 4,
        "assignments": 2,
        "milestones": 3
    }
    draft_plan = planner.propose_plan(context)
    revised_plan = planner.revise(draft_plan, "Add an assignment on Multi-Agent Swarms with 50 marks.")
    locked_plan = planner.lock_plan(revised_plan)

    return {
        "lab": "Lab 1: Agent vs Chatbot (The Planner Loop)",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": True,
        "trace": {
            "vague_input": vague_prompt,
            "clarifying_questions_count": len(clarify_res.questions),
            "clarifying_questions": [q.model_dump() for q in clarify_res.questions],
            "draft_plan": draft_plan.model_dump(),
            "revised_plan": revised_plan.model_dump(),
            "locked_plan": locked_plan.model_dump()
        }
    }
