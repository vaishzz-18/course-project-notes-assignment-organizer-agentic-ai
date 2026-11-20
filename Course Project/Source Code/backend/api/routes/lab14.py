"""
Lab 14: Capstone — Full Team-Owned Deployed System Route
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Endpoints:
  • GET  /lab14/demo                 — Full end-to-end capstone demonstration
  • GET  /lab14/status               — System health and integration status
  • POST /lab14/run                  — Execute the full capstone pipeline
  • POST /lab14/approve/{session_id} — Faculty approval gate
  • POST /lab14/publish/{session_id} — Governed publish with versioning
  • POST /lab14/rollback/{session_id}— One-click rollback
  • GET  /lab14/dashboard/{session_id}— Faculty dashboard view
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from runtime.capstone_system import (
    CapstoneSystem,
    CapstoneRequest,
)

router = APIRouter(prefix="/lab14", tags=["Lab 14: Capstone — Full Team-Owned Deployed System"])

# Shared system instance
capstone = CapstoneSystem()


class RunRequest(BaseModel):
    course_id: int = 1
    faculty_id: int = 1
    faculty_name: str = "Dr. Sarah Chen"
    request_text: str = "Generate complete course workspace for review."
    domain: str = "theory"


class ApproveRequest(BaseModel):
    faculty_id: int = 1
    faculty_name: str = "Dr. Sarah Chen"
    edits: Optional[Dict[str, Any]] = None


# ─── Demo Endpoint ────────────────────────────────────────────────────────

@router.get("/demo")
async def lab14_demo():
    """
    Lab 14 Capstone Demonstration: Full end-to-end pipeline.
    
    system = deploy(connector, runtime, graph, governance)
    artifact = system.run(request)
    dashboard.show(artifact, metrics, audit)
    """
    # Step 1: System status
    status = capstone.get_system_status()

    # Step 2: Run the full pipeline
    request = CapstoneRequest(
        course_id=1,
        faculty_id=1,
        faculty_name="Dr. Sarah Chen",
        request_text="Complete course workspace: notes, assignments, grades.",
        domain="theory",
    )
    artifact = capstone.run(request)

    # Step 3: Faculty approves
    approved = capstone.approve(
        session_id=artifact.session_id,
        faculty_id=1,
        faculty_name="Dr. Sarah Chen",
    )
    approved_status = approved.status
    approved_by = approved.governance_record.get("approved_by")

    # Step 4: Publish
    published = capstone.publish(session_id=artifact.session_id)

    # Step 5: Get dashboard view
    dashboard = capstone.dashboard(session_id=artifact.session_id)

    return {
        "status": "success",
        "lab": "Lab 14: Capstone — Full Team-Owned Deployed System",
        "pseudocode": "system = deploy(connector, runtime, graph, governance); "
                      "artifact = system.run(request); dashboard.show(artifact, metrics, audit)",
        "steps": {
            "step1_system_status": status,
            "step2_pipeline_execution": {
                "session_id": artifact.session_id,
                "stages_total": artifact.metrics["total_stages"],
                "stages_passed": artifact.metrics["passed"],
                "total_duration_ms": artifact.metrics["total_duration_ms"],
                "labs_integrated": artifact.metrics["labs_integrated"],
                "pipeline_stages": [
                    {
                        "stage": s.stage,
                        "lab": s.lab,
                        "status": s.status,
                        "summary": s.summary,
                    }
                    for s in artifact.pipeline_stages
                ],
            },
            "step3_faculty_approval": {
                "approved_by": approved_by,
                "status": approved_status,
            },
            "step4_governed_publish": {
                "status": published.status,
                "version": published.governance_record.get("version"),
            },
            "step5_faculty_dashboard": dashboard.to_dict(),
            "step6_validation_report": artifact.validation_report,
            "step7_audit_trail_count": len(artifact.audit_trail),
        },
    }


# ─── CRUD Endpoints ───────────────────────────────────────────────────────

@router.get("/status")
async def system_status():
    """Get full system health and integration status."""
    return capstone.get_system_status()


@router.post("/run")
async def run_pipeline(req: RunRequest):
    """Execute the full capstone pipeline."""
    request = CapstoneRequest(
        course_id=req.course_id,
        faculty_id=req.faculty_id,
        faculty_name=req.faculty_name,
        request_text=req.request_text,
        domain=req.domain,
    )
    artifact = capstone.run(request)
    return artifact.to_dict()


@router.post("/approve/{session_id}")
async def approve_artifact(session_id: str, req: ApproveRequest):
    """Faculty approval gate — the human decision point."""
    try:
        artifact = capstone.approve(
            session_id=session_id,
            faculty_id=req.faculty_id,
            faculty_name=req.faculty_name,
            edits=req.edits,
        )
        return {
            "status": "approved",
            "session_id": session_id,
            "approved_by": req.faculty_name,
            "governance_record": artifact.governance_record,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/publish/{session_id}")
async def publish_artifact(session_id: str):
    """Governed publish — versioned, auditable, reversible."""
    try:
        artifact = capstone.publish(session_id=session_id)
        return {
            "status": "published",
            "session_id": session_id,
            "version": artifact.governance_record.get("version"),
            "governance_record": artifact.governance_record,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollback/{session_id}")
async def rollback_artifact(session_id: str):
    """One-click rollback to previous version."""
    try:
        artifact = capstone.rollback(session_id=session_id)
        return {
            "status": "rolled_back",
            "session_id": session_id,
            "governance_record": artifact.governance_record,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")


@router.get("/dashboard/{session_id}")
async def get_dashboard(session_id: str):
    """Faculty dashboard view: notes, submissions, grades, milestones + system health."""
    try:
        dashboard = capstone.dashboard(session_id=session_id)
        return dashboard.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
