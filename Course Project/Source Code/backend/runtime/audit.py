import json
import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import AuditLog


class AuditLogger:
    def __init__(self, db: AsyncSession, run_id: str, actor_id: Optional[int] = None):
        self.db = db
        self.run_id = run_id
        self.actor_id = actor_id

    async def log(
        self,
        agent_name: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        entry = AuditLog(
            run_id=self.run_id,
            agent_name=agent_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            input_data=json.dumps(input_data, default=str) if input_data else None,
            output_data=json.dumps(output_data, default=str) if output_data else None,
            status=status,
            error_message=error_message,
            created_at=datetime.utcnow(),
            actor_id=self.actor_id,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def log_error(self, agent_name: str, action: str, error: Exception, input_data: Any = None):
        return await self.log(
            agent_name=agent_name,
            action=action,
            input_data=input_data,
            status="error",
            error_message=str(error),
        )


def new_run_id() -> str:
    return str(uuid.uuid4())
