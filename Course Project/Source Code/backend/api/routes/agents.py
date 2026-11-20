"""
AURA Seven-Agent System & Workflow Management Endpoints.
Exposes agent definitions, registry, workflow thread checkpoints, and human approval resume triggers.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, WorkflowThread, AuditLog, AgentMetrics
from agents.registry import AgentRegistry, SEVEN_CORE_AGENTS
from runtime.workflow_persistence_service import WorkflowPersistenceService
from api.routes.auth import require_faculty

router = APIRouter(prefix="/agents", tags=["AURA Seven-Agent System"])


@router.get("/")
async def list_core_agents():
    """Lists the official seven production agents, their roles, and capabilities."""
    return {
        "status": "success",
        "total_agents": len(SEVEN_CORE_AGENTS),
        "agents": AgentRegistry.get_all_agents(),
    }


@router.get("/{agent_id}")
async def get_agent_detail(agent_id: int):
    """Retrieves metadata and responsibilities for a specific registered agent."""
    try:
        return AgentRegistry.get_agent_by_id(agent_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent ID {agent_id} not found")


@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    """Retrieves recent telemetry, execution metrics, and audit logs for the specified agent."""
    try:
        agent = AgentRegistry.get_agent_by_id(agent_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent ID {agent_id} not found")

    agent_name = agent["name"]

    q_audit = (
        select(AuditLog)
        .where(AuditLog.agent_name == agent_name)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    audit_res = await db.execute(q_audit)
    recent_logs = [
        {
            "id": log.id,
            "run_id": log.run_id,
            "action": log.action,
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "error_message": log.error_message,
        }
        for log in audit_res.scalars().all()
    ]

    q_metrics = (
        select(AgentMetrics)
        .where(AgentMetrics.agent_name == agent_name)
        .order_by(AgentMetrics.created_at.desc())
        .limit(limit)
    )
    metrics_res = await db.execute(q_metrics)
    recent_metrics = [
        {
            "id": m.id,
            "run_id": m.run_id,
            "tool_name": m.tool_name,
            "execution_time_ms": m.execution_time_ms,
            "llm_latency_ms": m.llm_latency_ms,
            "token_input": m.token_input,
            "token_output": m.token_output,
            "success": m.success,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in metrics_res.scalars().all()
    ]

    return {
        "status": "success",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "role": agent["role"],
        "operational_status": "idle" if not recent_logs else "active",
        "total_audit_events": len(recent_logs),
        "recent_logs": recent_logs,
        "recent_metrics": recent_metrics,
    }


@router.get("/workflows/threads")
async def list_workflow_threads(faculty=Depends(require_faculty)):
    """Lists persisted LangGraph workflow threads and checkpoints."""
    svc = WorkflowPersistenceService()
    conn = svc._get_conn()
    c = conn.cursor()
    c.execute("SELECT thread_id, run_id, agent_name, current_node, workflow_status, approval_status, created_at, updated_at FROM workflow_threads ORDER BY updated_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"status": "success", "threads": rows}


@router.post("/workflows/{thread_id}/resume")
async def resume_workflow_thread(thread_id: str, faculty=Depends(require_faculty)):
    """Human-in-the-loop: Faculty grants approval to resume an interrupted LangGraph workflow."""
    svc = WorkflowPersistenceService()
    resumed = svc.record_approval_and_resume(thread_id, approver_id=faculty.id)
    if not resumed:
        raise HTTPException(status_code=404, detail=f"Workflow thread '{thread_id}' not found")
    return {
        "status": "success",
        "message": f"Workflow thread '{thread_id}' approved and marked for resumption",
        "thread": resumed,
    }
