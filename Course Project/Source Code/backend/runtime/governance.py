import json
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import RunContext, Grade, GradeStatus
from runtime.audit import AuditLogger


class GovernanceEngine:
    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def create_run(self, run_id: str, plan: dict, created_by: Optional[int] = None) -> RunContext:
        ctx = RunContext(
            run_id=run_id,
            status="running",
            plan=json.dumps(plan, default=str),
            state=json.dumps({}),
            version=1,
            attempts=0,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )
        self.db.add(ctx)
        await self.db.flush()
        await self.audit.log("GovernanceEngine", "run_created", input_data={"plan": plan})
        return ctx

    async def checkpoint(self, run_id: str, state: dict):
        result = await self.db.execute(select(RunContext).where(RunContext.run_id == run_id))
        ctx = result.scalar_one_or_none()
        if ctx:
            ctx.state = json.dumps(state, default=str)
            await self.db.flush()

    async def complete_run(self, run_id: str):
        result = await self.db.execute(select(RunContext).where(RunContext.run_id == run_id))
        ctx = result.scalar_one_or_none()
        if ctx:
            ctx.status = "completed"
            ctx.completed_at = datetime.utcnow()
            await self.db.flush()

    async def fail_run(self, run_id: str, reason: str):
        result = await self.db.execute(select(RunContext).where(RunContext.run_id == run_id))
        ctx = result.scalar_one_or_none()
        if ctx:
            ctx.status = "failed"
            ctx.completed_at = datetime.utcnow()
            await self.db.flush()
        await self.audit.log("GovernanceEngine", "run_failed", output_data={"reason": reason}, status="error")

    async def publish_grade(self, grade_id: int, approver_id: int, edits: Optional[dict] = None) -> Grade:
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade {grade_id} not found")
        if grade.status not in (GradeStatus.pending_approval, GradeStatus.approved):
            raise ValueError(f"Grade {grade_id} is not awaiting approval (status={grade.status})")

        if edits:
            if "marks" in edits:
                grade.final_marks = edits["marks"]
            if "feedback" in edits:
                grade.final_feedback = edits["feedback"]
        else:
            grade.final_marks = grade.draft_marks
            grade.final_feedback = grade.draft_feedback

        grade.status = GradeStatus.published
        grade.approved_by = approver_id
        grade.approved_at = datetime.utcnow()
        grade.published_at = datetime.utcnow()
        await self.db.flush()

        await self.audit.log(
            "GovernanceEngine", "grade_published",
            entity_type="Grade", entity_id=grade_id,
            input_data={"edits": edits},
            output_data={"final_marks": grade.final_marks},
        )
        return grade

    async def rollback_grade(self, grade_id: int, version: int = 0) -> Grade:
        """Roll back a published grade to draft state."""
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade {grade_id} not found")

        grade.status = GradeStatus.draft
        grade.final_marks = None
        grade.final_feedback = None
        grade.approved_by = None
        grade.approved_at = None
        grade.published_at = None
        await self.db.flush()

        await self.audit.log(
            "GovernanceEngine", "grade_rolled_back",
            entity_type="Grade", entity_id=grade_id,
        )
        return grade
