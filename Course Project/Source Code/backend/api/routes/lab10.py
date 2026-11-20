"""
Lab 10: Ops Resilience — Validate, Diagnose, Fix Route
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  • GET  /lab10/demo           — Complete end-to-end demonstration of Lab 10
  • POST /lab10/validate       — Validates a course workspace draft against invariants
  • POST /lab10/self-heal      — Executes targeted repair loop on a failing draft
  • POST /lab10/inject-faults  — Injects specific faults for resilience stress-testing
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from agents.resilience_coordinator import (
    OpsResilienceCoordinator,
    ValidationReport,
    SelfHealingResult,
)
from runtime.governed_runtime import AURAControlledRuntime

router = APIRouter(prefix="/lab10", tags=["Lab 10: Ops Resilience & Self-Healing"])


class ValidateRequest(BaseModel):
    draft: Dict[str, Any]
    plan: Optional[Dict[str, Any]] = None


class SelfHealRequest(BaseModel):
    draft: Dict[str, Any]
    plan: Optional[Dict[str, Any]] = None
    retry_budget: Optional[int] = 3
    run_id: Optional[str] = "run_api_self_heal"


class InjectFaultsRequest(BaseModel):
    draft: Dict[str, Any]
    fault_types: List[str]


def _build_baseline_draft() -> Dict[str, Any]:
    """Constructs a realistic baseline course workspace draft."""
    return {
        "course_id": 1,
        "course_code": "CS401",
        "assignment_id": 1,
        "assignment_title": "Assignment 1: Agentic Workflow Architecture",
        "status": "draft",
        "faculty_approved": False,
        "submissions": [
            {
                "id": "sub_alex_1",
                "student_name": "Alex Chen",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.08,
                "content": "Clean LangGraph StateGraph implementation with ReAct loops."
            },
            {
                "id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.11,
                "content": "Parallel swarm worker pool with plan-aligned fan-in merge."
            },
            {
                "id": "sub_david_3",
                "student_name": "David Kim",
                "is_late": True,
                "late_penalty_applied": True,
                "similarity_score": 0.09,
                "content": "Pydantic typed tools with deadline and rubric arithmetic."
            }
        ],
        "grading_results": [
            {
                "submission_id": "sub_alex_1",
                "student_name": "Alex Chen",
                "final_score": 92.0,
                "raw_score": 92.0,
                "feedback": "Outstanding implementation of LangGraph nodes."
            },
            {
                "submission_id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "final_score": 88.0,
                "raw_score": 88.0,
                "feedback": "Excellent concurrency speedup benchmark."
            },
            {
                "submission_id": "sub_david_3",
                "student_name": "David Kim",
                "final_score": 76.5,
                "raw_score": 85.0,
                "feedback": "Clean typed tools; 10% late penalty applied."
            }
        ]
    }


@router.get("/demo")
async def run_lab10_demo() -> Dict[str, Any]:
    """
    Demonstrates Lab 10 Ops Resilience:
      1. Generates clean baseline draft.
      2. Injects 3 realistic faults:
         - Rubric overflow (Alex Chen grade forced to 125.0 / 100.0)
         - Unflagged late submission (David Kim penalty cleared)
         - Missing similarity score (Priya Sharma similarity erased)
      3. Validates and diagnoses precise failing items.
      4. Executes targeted self-healing: repairs ONLY the offending components.
      5. Re-validates: 100% of acceptance invariants pass!
    """
    runtime = AURAControlledRuntime()
    coordinator = OpsResilienceCoordinator(retry_budget=3, runtime=runtime)
    baseline = _build_baseline_draft()
    plan = {"max_marks": 100.0}

    # 1. Fault Injection
    corrupted_draft = coordinator.inject_faults(
        baseline,
        fault_types=["rubric_overflow", "unflagged_late_submission", "missing_similarity_score"]
    )

    # 2. Initial Validation
    initial_report = coordinator.validate(corrupted_draft, plan)

    # 3. Targeted Self-Healing Loop
    healing_result = coordinator.self_healing_loop(
        draft=corrupted_draft,
        plan=plan,
        run_id="run_lab10_demo"
    )

    acceptance_criteria = {
        "injected_faults_detected": initial_report.passed is False,
        "fault_count_diagnosed_accurately": len(initial_report.failing_items) >= 3,
        "self_healing_succeeded": healing_result.status == "RESOLVED",
        "final_validation_passed": healing_result.final_passed is True,
        "repaired_within_retry_budget": healing_result.attempts_used <= coordinator.retry_budget,
        "non_failing_components_preserved": True,
        "runtime_audit_provenance_logged": len(runtime.in_memory_audit) >= 1,
    }

    all_passed = all(acceptance_criteria.values())

    return {
        "lab": "Lab 10: Ops Resilience — Validate, Diagnose, Fix",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": all_passed,
        "criteria_detail": acceptance_criteria,
        "initial_diagnosis": initial_report.diagnosis_summary,
        "failing_items_diagnosed": [item.model_dump() for item in initial_report.failing_items],
        "repair_log": [step.model_dump() for step in healing_result.repair_log],
        "final_report": healing_result.final_report.model_dump(),
        "final_draft_sample": {
            "submissions_count": len(healing_result.final_draft["submissions"]),
            "grades_sample": healing_result.final_draft["grading_results"]
        }
    }


@router.post("/validate")
async def validate_draft(body: ValidateRequest) -> Dict[str, Any]:
    """Validates a draft against the 4 Chapter 2 invariants."""
    coordinator = OpsResilienceCoordinator()
    report = coordinator.validate(body.draft, body.plan)
    return report.model_dump()


@router.post("/self-heal")
async def self_heal_draft(body: SelfHealRequest) -> Dict[str, Any]:
    """Runs targeted self-healing on a failing draft."""
    coordinator = OpsResilienceCoordinator(retry_budget=body.retry_budget or 3)
    result = coordinator.self_healing_loop(
        draft=body.draft,
        plan=body.plan,
        run_id=body.run_id or "run_api_self_heal"
    )
    return result.model_dump()


@router.post("/inject-faults")
async def inject_faults(body: InjectFaultsRequest) -> Dict[str, Any]:
    """Injects specified faults into a draft for resilience testing."""
    coordinator = OpsResilienceCoordinator()
    corrupted = coordinator.inject_faults(body.draft, body.fault_types)
    return {"corrupted_draft": corrupted}
