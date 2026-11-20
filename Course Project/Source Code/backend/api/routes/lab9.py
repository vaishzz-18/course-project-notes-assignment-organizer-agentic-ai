"""
Lab 9: Deep Research — Grounding & Evidence Route
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  • GET  /lab9/demo             — Complete end-to-end demonstration of Lab 9
  • GET  /lab9/syllabus-sources — Returns the approved syllabus & rubric ground truth
  • POST /lab9/ground-candidate — Researches & grounds a single candidate submission
  • POST /lab9/audit-batch      — Runs grounding filter over a batch of submissions
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.grounding_agent import (
    EvidenceGroundingAgent,
    EvidenceRecord,
    GroundedCandidate,
    EvidenceTable,
    DEFAULT_APPROVED_SYLLABUS,
)
from runtime.governed_runtime import AURAControlledRuntime

router = APIRouter(prefix="/lab9", tags=["Lab 9: Deep Research & Evidence Grounding"])


class GroundCandidateRequest(BaseModel):
    candidate_id: str
    content: str
    candidate_title: Optional[str] = "Assignment Submission"
    student_name: Optional[str] = "Anonymous Student"
    student_id: Optional[int] = None


class BatchAuditRequest(BaseModel):
    course_code: Optional[str] = "CS401"
    course_name: Optional[str] = "Agentic AI & Autonomous Systems"
    assignment_title: Optional[str] = "Assignment 1: Agentic Workflow Architecture"
    submissions: List[Dict[str, Any]]


@router.get("/demo")
async def run_lab9_demo() -> Dict[str, Any]:
    """
    Demonstrates Lab 9 Deep Research grounding on realistic sample candidates:
      • 3 In-Scope candidates (grounded in LangGraph, ReAct loops, Swarms, Tools)
      • 2 Ungrounded / Out-of-Scope candidates (Quantum annealing, Blockchain mining)
    Verifies that in-scope items are accepted with citations and out-of-scope items are rejected.
    """
    runtime = AURAControlledRuntime()
    agent = EvidenceGroundingAgent(runtime=runtime)

    demo_submissions = [
        {
            "id": "sub_alex_001",
            "student_name": "Alex Chen",
            "student_id": 5,
            "title": "LangGraph ReAct Cognitive Loop Submission",
            "content": (
                "Our implementation builds an agentic workflow using LangGraph StateGraph with explicit nodes. "
                "The planner loop executes ReAct reasoning cycles to clarify requirements and propose plans. "
                "All calculations call typed tools to guarantee zero hallucination."
            )
        },
        {
            "id": "sub_priya_002",
            "student_name": "Priya Sharma",
            "student_id": 6,
            "title": "Parallel Swarm Worker Pipeline",
            "content": (
                "This submission implements a parallel swarm using asyncio.gather for fan-out processing of student tasks. "
                "The coordinator merges worker drafts strictly aligned to the locked course plan. "
                "StateGraph back-edges provide self-healing conditional retry routing."
            )
        },
        {
            "id": "sub_david_003",
            "student_name": "David Kim",
            "student_id": 9,
            "title": "Typed Tool Invariant Verification",
            "content": (
                "We designed typed tools for deadline calculation and rubric checking using Pydantic schemas. "
                "The agent loop enforces zero hallucination math, ensuring grades and similarity scores are strictly tool-computed."
            )
        },
        {
            "id": "sub_hallucinated_004",
            "student_name": "Out-of-Scope Candidate 1",
            "student_id": 99,
            "title": "Quantum Annealing Optimization for Grade Prediction",
            "content": (
                "We utilized D-Wave quantum annealing adiabatic Hamiltonians to calculate student marks. "
                "Superposition states determine whether an assignment is accepted or rejected."
            )
        },
        {
            "id": "sub_hallucinated_005",
            "student_name": "Out-of-Scope Candidate 2",
            "student_id": 98,
            "title": "Smart Contract Blockchain Mining for Course Credits",
            "content": (
                "This project uses Ethereum smart contract proof-of-work blockchain mining to store grades on-chain. "
                "Miners validate hashes before distributing tokens."
            )
        }
    ]

    candidates, evidence_table = agent.evaluate_batch(
        submissions=demo_submissions,
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
        assignment_title="Assignment 1: Agentic Workflow Architecture"
    )

    acceptance_criteria = {
        "each_candidate_carries_evidence_record": all(c.evidence is not None for c in candidates),
        "paper_level_evidence_table_produced": evidence_table.total_candidates == 5,
        "grounded_candidates_accepted": sum(1 for c in candidates if c.status == "GROUNDED") == 3,
        "ungrounded_candidates_rejected": sum(1 for c in candidates if c.status == "REJECTED") == 2,
        "all_rejected_have_rejection_reasons": all(
            c.evidence.rejection_reason is not None for c in candidates if c.status == "REJECTED"
        ),
        "governed_by_runtime_audit": len(runtime.in_memory_audit) >= 5,
    }

    all_passed = all(acceptance_criteria.values())

    return {
        "lab": "Lab 9: Deep Research — Ground & Evidence",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": all_passed,
        "criteria_detail": acceptance_criteria,
        "evidence_table": evidence_table.model_dump(),
        "grounded_candidates_sample": [c.model_dump() for c in candidates[:3]],
        "rejected_candidates_sample": [c.model_dump() for c in candidates[3:]],
        "audit_trace_count": len(runtime.in_memory_audit),
    }


@router.get("/syllabus-sources")
async def get_syllabus_sources() -> Dict[str, Any]:
    """Returns the faculty-approved syllabus and rubric source truth used for grounding."""
    return DEFAULT_APPROVED_SYLLABUS


@router.post("/ground-candidate")
async def ground_candidate(body: GroundCandidateRequest) -> Dict[str, Any]:
    """Researches and grounds a single submission, returning its evidence record."""
    agent = EvidenceGroundingAgent()
    candidate = agent.evaluate_submission(
        candidate_id=body.candidate_id,
        content=body.content,
        student_name=body.student_name or "Student",
        student_id=body.student_id,
        candidate_title=body.candidate_title or "Assignment Submission",
    )
    return candidate.model_dump()


@router.post("/audit-batch")
async def audit_batch(body: BatchAuditRequest) -> Dict[str, Any]:
    """Runs grounding and produces the paper-level evidence table across a batch."""
    agent = EvidenceGroundingAgent()
    candidates, table = agent.evaluate_batch(
        submissions=body.submissions,
        course_code=body.course_code or "CS401",
        course_name=body.course_name or "Agentic AI",
        assignment_title=body.assignment_title or "Course Assignment",
    )
    return {
        "evidence_table": table.model_dump(),
        "candidates": [c.model_dump() for c in candidates],
    }
