from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import AuditLog, get_db
from api.routes.auth import require_faculty

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def get_audit_log(
    run_id: str = None,
    limit: int = 100,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if run_id:
        q = select(AuditLog).where(AuditLog.run_id == run_id).order_by(AuditLog.created_at)
    result = await db.execute(q)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "run_id": l.run_id,
            "agent_name": l.agent_name,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "status": l.status,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
