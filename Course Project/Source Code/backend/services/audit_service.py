"""
AuditService — Immutable structured audit logger.
Ensures every agent run, tool call, and governance action is auditable.
Sanitizes sensitive data (passwords, tokens) before persistence.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import AuditLog

SENSITIVE_KEYS = {"password", "token", "secret", "gemini_api_key", "password_hash"}


def sanitize_payload(payload: Any) -> Any:
    """Recursively redacts sensitive keys from audit log payloads."""
    if isinstance(payload, dict):
        cleaned = {}
        for k, v in payload.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_payload(v)
        return cleaned
    elif isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    return payload


class AuditService:
    def __init__(self, db: AsyncSession, run_id: Optional[str] = None, actor_id: Optional[int] = None):
        self.db = db
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        self.actor_id = actor_id

    async def log_event(
        self,
        agent_name: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Persists an append-only sanitized audit record."""
        clean_input = json.dumps(sanitize_payload(input_data), default=str) if input_data else None
        clean_output = json.dumps(sanitize_payload(output_data), default=str) if output_data else None

        entry = AuditLog(
            run_id=self.run_id,
            agent_name=agent_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            input_data=clean_input,
            output_data=clean_output,
            status=status,
            error_message=error_message,
            actor_id=self.actor_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
