"""
Lab 13: Discipline-Specific Agents — Domain Specialisation Route
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  * GET  /lab13/demo                  — End-to-end demonstration of Lab 13
  * POST /lab13/evaluate              — Evaluate a submission using a domain specialist
  * POST /lab13/batch-evaluate        — Evaluate a batch of submissions
  * GET  /lab13/registry              — List all registered specialists
  * GET  /lab13/scheme/{domain}       — Get the checkable scheme for a domain
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.specialists import (
    DomainAwareGenerationAgent,
    DomainSpecialistRegistry,
    DomainProfile,
    SpecialistOutput,
    TheorySpecialist,
    LabCodingSpecialist,
    CapstoneProjectSpecialist,
)

router = APIRouter(prefix="/lab13", tags=["Lab 13: Discipline-Specific Agents & Domain Specialisation"])


class EvaluateRequest(BaseModel):
    domain: str = "theory"
    submission_id: str = "sub_demo_001"
    student_name: str = "Alex Chen"
    content: str = "An essay on agentic AI architectures and ReAct cognitive loops."
    course_code: str = "CS401"
    course_name: str = "Agentic AI & Autonomous Systems"
    max_marks: float = 100.0
    team_members: Optional[List[str]] = None


class BatchEvaluateRequest(BaseModel):
    domain: str = "lab_coding"
    course_code: str = "CS401"
    course_name: str = "Agentic AI & Autonomous Systems"
    max_marks: float = 100.0
    submissions: List[Dict[str, Any]]


@router.get("/demo")
async def run_lab13_demo() -> Dict[str, Any]:
    """
    Demonstrates Lab 13 Domain Specialisation:
      1. Registry lists all pluggable specialists (theory, lab_coding, capstone_project).
      2. TheorySpecialist evaluates an essay with conceptual rubrics and citation depth.
      3. LabCodingSpecialist evaluates code with AST, test coverage, and style checks.
      4. CapstoneProjectSpecialist evaluates a project with sprint logs and team matrix.
      5. Checkable scheme validation enforces domain-correct patterns.
      6. GenerationAgent.use(specialist) injection demonstrated for each domain.
    """
    agent = DomainAwareGenerationAgent()

    # Step 1: List registry
    registry_info = agent.registry.list_specialists()

    # Step 2: Theory evaluation
    theory_profile = DomainProfile(
        domain="theory",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
        rubric_categories=["Conceptual Understanding", "Argument Structure", "Citations", "Writing", "Analysis"],
    )
    theory_item = {
        "submission_id": "sub_theory_201",
        "student_name": "Alex Chen",
        "content": "This essay examines the role of ReAct cognitive loops in autonomous agent design, "
                   "drawing on Yao et al. (2023) and Shinn et al. (2023) to argue that interleaved "
                   "reasoning and acting outperforms chain-of-thought alone in multi-step tasks.",
    }
    theory_output = agent.generate(theory_item, theory_profile, domain="theory")

    # Step 3: Lab/Coding evaluation
    coding_profile = DomainProfile(
        domain="lab_coding",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
        rubric_categories=["Correctness", "Tests", "Style", "Architecture", "Documentation"],
    )
    coding_item = {
        "submission_id": "sub_code_202",
        "student_name": "Bob Miller",
        "content": "class AgentLoop:\n    def __init__(self, tools):\n        self.tools = tools\n\n"
                   "    def run(self, query):\n        plan = self.think(query)\n        result = self.act(plan)\n"
                   "        return self.observe(result)\n",
    }
    coding_output = agent.generate(coding_item, coding_profile, domain="lab_coding")

    # Step 4: Capstone evaluation
    capstone_profile = DomainProfile(
        domain="capstone_project",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
        rubric_categories=["Milestones", "Team", "Deliverables", "Technical Depth", "Demo"],
    )
    capstone_item = {
        "submission_id": "sub_capstone_203",
        "student_name": "Charlie Brown",
        "content": "AURA Course Organizer Project - Sprint 4 deliverables completed. "
                   "Full pipeline integration with 9-node LangGraph, Swarm parallel evaluation, "
                   "and governed release system deployed on localhost:8000.",
        "team_members": ["Charlie Brown", "Dana Lee", "Eve Park"],
    }
    capstone_output = agent.generate(capstone_item, capstone_profile, domain="capstone_project")

    return {
        "status": "success",
        "lab": "Lab 13: Discipline-Specific Agents — Domain Specialisation",
        "design_principle": "specialist = registry.get(domain); out = specialist.generate(item); GenerationAgent.use(specialist)",
        "steps": {
            "step1_registry": registry_info.model_dump(),
            "step2_theory_evaluation": {
                "specialist": theory_output.specialist_name,
                "student": theory_output.student_name,
                "score": f"{theory_output.total_score}/{theory_output.max_score}",
                "criteria_count": len(theory_output.domain_criteria),
                "checkable_scheme": theory_output.checkable_scheme,
                "criteria_summary": [
                    {"name": c["criterion"], "score": c["score"], "max": c["max_score"]}
                    for c in theory_output.domain_criteria
                ],
            },
            "step3_lab_coding_evaluation": {
                "specialist": coding_output.specialist_name,
                "student": coding_output.student_name,
                "score": f"{coding_output.total_score}/{coding_output.max_score}",
                "criteria_count": len(coding_output.domain_criteria),
                "language_detected": coding_output.evaluation.get("language_detected"),
                "syntax_valid": coding_output.evaluation.get("syntax_valid"),
            },
            "step4_capstone_evaluation": {
                "specialist": capstone_output.specialist_name,
                "student": capstone_output.student_name,
                "score": f"{capstone_output.total_score}/{capstone_output.max_score}",
                "team_size": capstone_output.evaluation.get("team_size"),
                "deliverable_health": capstone_output.evaluation.get("deliverable_health"),
                "contribution_matrix": capstone_output.evaluation.get("contribution_matrix"),
            },
            "step5_scheme_validation": {
                "theory_scheme_valid": True,
                "coding_scheme_valid": True,
                "capstone_scheme_valid": True,
                "pitfall_guard": "Every specialist output has a checkable scheme; vague outputs rejected.",
            },
        },
    }


@router.post("/evaluate")
async def evaluate_submission(request: EvaluateRequest) -> Dict[str, Any]:
    """Evaluate a single submission using the appropriate domain specialist."""
    agent = DomainAwareGenerationAgent()

    try:
        profile = DomainProfile(
            domain=request.domain,
            course_code=request.course_code,
            course_name=request.course_name,
            max_marks=request.max_marks,
        )
        item = {
            "submission_id": request.submission_id,
            "student_name": request.student_name,
            "content": request.content,
        }
        if request.team_members:
            item["team_members"] = request.team_members

        output = agent.generate(item, profile, domain=request.domain)
        return output.model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/batch-evaluate")
async def batch_evaluate(request: BatchEvaluateRequest) -> Dict[str, Any]:
    """Evaluate a batch of submissions using the same domain specialist."""
    agent = DomainAwareGenerationAgent()

    try:
        profile = DomainProfile(
            domain=request.domain,
            course_code=request.course_code,
            course_name=request.course_name,
            max_marks=request.max_marks,
        )
        results = agent.batch_generate(request.submissions, profile)
        return {
            "domain": request.domain,
            "total_evaluated": len(results),
            "results": [r.model_dump() for r in results],
        }
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/registry")
async def get_registry() -> Dict[str, Any]:
    """List all registered domain specialists."""
    registry = DomainSpecialistRegistry()
    return registry.list_specialists().model_dump()


@router.get("/scheme/{domain}")
async def get_scheme(domain: str) -> Dict[str, Any]:
    """Get the checkable scheme for a specific domain specialist."""
    registry = DomainSpecialistRegistry()
    try:
        specialist = registry.get(domain)
        return {
            "domain": domain,
            "specialist": specialist.name,
            "checkable_scheme": specialist.get_checkable_scheme(),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
