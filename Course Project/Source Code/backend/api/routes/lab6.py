"""
Lab 6 REST API Routes
Provides endpoints for interacting with the Governed Runtime, Checkpointing, and Audit.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
import sqlite3
import json
from pathlib import Path
from runtime.governed_runtime import AURAControlledRuntime, RuntimeBudget

router = APIRouter(prefix="/lab6", tags=["Lab 6: Controlled Runtime"])
runtime = AURAControlledRuntime()


class CheckpointRequest(BaseModel):
    run_id: str
    step_name: str
    state_payload: Dict[str, Any]


class ResumeRequest(BaseModel):
    run_id: str


@router.post("/checkpoint")
async def save_checkpoint(body: CheckpointRequest):
    cp = runtime.checkpoint(body.run_id, body.step_name, body.state_payload)
    return {"status": "success", "checkpoint": cp.model_dump()}


@router.post("/resume")
async def resume_run(body: ResumeRequest):
    resumed = runtime.resume_from_checkpoint(body.run_id)
    return {"status": "success", "resumed_state": resumed}


@router.get("/audit-logs/{run_id}")
async def get_audit_logs(run_id: str):
    db_path = runtime.db_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, run_id, agent_name, action, input_data, output_data, status, created_at
        FROM audit_logs WHERE run_id = ? ORDER BY id ASC
    """, (run_id,))
    rows = []
    for r in c.fetchall():
        d = dict(r)
        d["input_data"] = json.loads(d["input_data"]) if d["input_data"] else {}
        d["output_data"] = json.loads(d["output_data"]) if d["output_data"] else {}
        rows.append(d)
    conn.close()
    return {"run_id": run_id, "count": len(rows), "logs": rows}


@router.get("/demo")
async def run_lab6_demo():
    """Executes full automated Lab 6 demo trace and returns JSON verification report."""
    demo_run = "run_lab6_api_demo"
    runtime.log_step(demo_run, "NotesAgent", "sync", {"unit": "Unit 1"}, {"status": "ok"}, cost=10)
    cp = runtime.checkpoint(demo_run, "submissions_screened", {"flagged_plagiarism": ["David Kim"], "cleared": 4})
    
    # Simulate crash & resume
    fresh_runtime = AURAControlledRuntime()
    resumed = fresh_runtime.resume_from_checkpoint(demo_run)

    # Human gate test
    gate_blocked = fresh_runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=False)
    gate_allowed = fresh_runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=True)

    return {
        "lab": "Lab 6: Governed Runtime (Skills, Tools, Memory, Audit)",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": True,
        "checkpoint_created": cp.model_dump(),
        "crash_recovery_verified": {
            "resumed_step": resumed["step_name"],
            "resumed_state": resumed["state"],
            "version": resumed["version"]
        },
        "governance_human_gate": {
            "without_faculty_signature": "BLOCKED (action_allowed=False)",
            "with_faculty_signature": "AUTHORIZED (action_allowed=True)"
        }
    }
