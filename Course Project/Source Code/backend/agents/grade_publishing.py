"""Grade Publishing & Archive Agent — publishes faculty-approved grades with full audit trail."""
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Grade, GradeStatus, Submission, Assignment
from runtime.audit import AuditLogger
from runtime.governance import GovernanceEngine


class GradePublishingAgent:
    AGENT_NAME = "GradePublishingAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger, governance: GovernanceEngine):
        self.db = db
        self.audit = audit
        self.governance = governance

    async def step(self, grade_id: int, approver_id: int, edits: Optional[dict] = None) -> Grade:
        """Pipeline step: publish a faculty-approved grade."""
        grade = await self.governance.publish_grade(grade_id, approver_id, edits)
        await self.audit.log(
            self.AGENT_NAME, "grade_published_and_archived",
            entity_type="Grade", entity_id=grade_id,
            output_data={"final_marks": grade.final_marks, "approved_by": approver_id},
        )
        return grade

    async def bulk_publish(self, grade_ids: List[int], approver_id: int) -> List[Grade]:
        grades = []
        for gid in grade_ids:
            grade = await self.step(gid, approver_id)
            grades.append(grade)
        return grades

    async def rollback(self, grade_id: int, approver_id: int) -> Grade:
        grade = await self.governance.rollback_grade(grade_id)
        await self.audit.log(
            self.AGENT_NAME, "grade_rolled_back",
            entity_type="Grade", entity_id=grade_id,
            input_data={"rolled_back_by": approver_id},
        )
        return grade

    async def get_published_summary(self, assignment_id: int) -> List[dict]:
        q = (
            select(Grade, Submission)
            .join(Submission, Grade.submission_id == Submission.id)
            .where(Submission.assignment_id == assignment_id)
            .where(Grade.status == GradeStatus.published)
        )
        result = await self.db.execute(q)
        rows = result.all()
        return [
            {
                "grade_id": g.id,
                "submission_id": g.submission_id,
                "student_id": s.student_id,
                "final_marks": g.final_marks,
                "final_feedback": g.final_feedback,
                "published_at": g.published_at.isoformat() if g.published_at else None,
                "approved_by": g.approved_by,
            }
            for g, s in rows
        ]
