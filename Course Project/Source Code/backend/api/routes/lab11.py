"""
Lab 11: SDLC Factory — Spec → Tested Output Route
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  • GET  /lab11/demo          — Complete end-to-end demonstration of Lab 11
  • POST /lab11/build         — Runs factory build: plan → workspace artifact + test report
  • POST /lab11/verify-gate   — Enforces gate: require report.all_pass before faculty review
  • GET  /lab11/spec-template — Returns canonical locked plan specification template
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from agents.sdlc_factory import (
    SDLCWorkspaceFactory,
    BuildArtifact,
    AcceptanceReport,
    GateVerificationResult,
)
from runtime.governed_runtime import AURAControlledRuntime

router = APIRouter(prefix="/lab11", tags=["Lab 11: SDLC Factory & Automated Acceptance Gate"])


class BuildRequest(BaseModel):
    course_id: Optional[int] = 1
    faculty_id: Optional[int] = 1
    plan: Optional[Dict[str, Any]] = None


class VerifyGateRequest(BaseModel):
    artifact: Dict[str, Any]


def _get_canonical_plan() -> Dict[str, Any]:
    """Returns the locked specification for CS401."""
    return {
        "course_code": "CS401",
        "course_name": "Agentic AI & Autonomous Systems",
        "faculty": "Dr. Vaishnavi Patel",
        "max_marks": 100.0,
        "units": [
            {"unit": "Unit 1", "title": "ReAct Cognitive Loops & Planner Engines"},
            {"unit": "Unit 2", "title": "Tool-Using Agents & Zero-Hallucination Math"},
            {"unit": "Unit 3", "title": "LangGraph StateGraphs & Back-Edges"},
            {"unit": "Unit 4", "title": "Parallel Multi-Agent Swarms"}
        ],
        "assignments": [
            {
                "id": 1,
                "title": "Assignment 1: Agentic Workflow Architecture",
                "max_marks": 100.0,
                "due_date": "2026-10-15T23:59:59Z"
            }
        ],
        "milestones": [
            {"checkpoint": 1, "title": "Core Agentic Architecture", "week": 4},
            {"checkpoint": 2, "title": "Swarm Benchmarking", "week": 8}
        ]
    }


@router.get("/demo")
async def run_lab11_demo() -> Dict[str, Any]:
    """
    Demonstrates Lab 11 SDLC Factory:
      1. Treats locked plan as a formal software specification.
      2. Executes factory build: artifact = build(plan).
      3. Evaluates 12-point automated acceptance suite: report = acceptance_suite(artifact, plan).
      4. Demonstrates passing gate: require report.all_pass -> ADVANCED_TO_FACULTY.
      5. Demonstrates failing gate: an invalid artifact is strictly BLOCKED from reaching faculty.
    """
    runtime = AURAControlledRuntime()
    factory = SDLCWorkspaceFactory(runtime=runtime)
    spec = _get_canonical_plan()

    # 1. Clean Build
    artifact = await factory.build_async(plan=spec, course_id=1, faculty_id=1, run_self_healing=True)

    # 2. Acceptance Test Suite
    report = factory.run_acceptance_suite(artifact, plan_spec=spec)

    # 3. Gate Verification (Clean Artifact)
    gate_clean = factory.verify_and_advance_to_faculty(artifact)

    # 4. Demonstrate Gate Blocking Corrupted Artifact (Negative Test)
    corrupted_artifact = artifact.model_copy(deep=True)
    corrupted_artifact.workspace["grading_results"][0]["final_score"] = 145.0  # Rubric violation
    corrupted_report = factory.run_acceptance_suite(corrupted_artifact, plan_spec=spec)
    gate_blocked = factory.verify_and_advance_to_faculty(corrupted_artifact)

    acceptance_criteria = {
        "build_command_produces_artifact": artifact.build_id is not None,
        "automated_12_point_suite_executed": report.total_tests == 12,
        "all_tests_passed_on_clean_build": report.all_pass is True,
        "clean_artifact_advanced_to_faculty": gate_clean.gate_status == "ADVANCED_TO_FACULTY",
        "corrupted_artifact_blocked_at_gate": gate_blocked.gate_status == "BLOCKED_BY_ACCEPTANCE_GATE",
        "governed_by_runtime_audit": len(runtime.in_memory_audit) >= 1,
    }

    all_passed = all(acceptance_criteria.values())

    return {
        "lab": "Lab 11: SDLC Factory — Spec → Tested Output",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": all_passed,
        "criteria_detail": acceptance_criteria,
        "build_metadata": {
            "build_id": artifact.build_id,
            "course": artifact.course_code,
            "build_time_ms": artifact.build_time_ms,
            "built_at": artifact.built_at,
        },
        "acceptance_report": report.model_dump(),
        "gatekeeper_clean": gate_clean.model_dump(),
        "gatekeeper_blocked_demo": gate_blocked.model_dump(),
        "audit_trace_count": len(runtime.in_memory_audit),
    }


@router.post("/build")
async def build_workspace(body: BuildRequest) -> Dict[str, Any]:
    """Executes SDLC build from plan spec and runs acceptance test suite."""
    runtime = AURAControlledRuntime()
    factory = SDLCWorkspaceFactory(runtime=runtime)
    spec = body.plan or _get_canonical_plan()

    artifact = await factory.build_async(
        plan=spec,
        course_id=body.course_id or 1,
        faculty_id=body.faculty_id or 1,
        run_self_healing=True
    )
    report = factory.run_acceptance_suite(artifact, plan_spec=spec)
    gate = factory.verify_and_advance_to_faculty(artifact)

    return {
        "artifact": artifact.model_dump(),
        "report": report.model_dump(),
        "gate": gate.model_dump(),
    }


@router.get("/spec-template")
async def get_spec_template() -> Dict[str, Any]:
    """Returns canonical locked plan specification."""
    return _get_canonical_plan()
