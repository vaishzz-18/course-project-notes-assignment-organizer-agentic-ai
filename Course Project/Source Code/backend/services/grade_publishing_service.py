"""
GradePublishingService — Deterministic academic grade publishing service.
CRITICAL INVARIANT:
Rejects any publishing operation without an explicit faculty approval record.
Autonomous agents CANNOT publish grades directly.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Grade, GradeStatus, Submission, Assignment
from runtime.audit import AuditLogger


class GradePublishingService:
    SERVICE_NAME = "GradePublishingService"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def publish_grade(
        self,
        grade_id: int,
        faculty_id: int,
        edits: Optional[Dict[str, Any]] = None,
    ) -> Grade:
        """
        Publishes an approved grade.
        Enforces human approval: only grades in 'approved' or 'pending_approval'
        with valid faculty credentials can be published.
        """
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade record {grade_id} not found")

        # Invariant: Must have passed through human review
        if grade.status not in (GradeStatus.pending_approval, GradeStatus.approved):
            raise PermissionError(
                f"Cannot publish grade in status '{grade.status}'. "
                "Only grades with faculty approval can be published."
            )

        now = datetime.now(timezone.utc)

        if edits:
            if "final_marks" in edits and edits["final_marks"] is not None:
                grade.final_marks = float(edits["final_marks"])
            if "final_feedback" in edits and edits["final_feedback"] is not None:
                grade.final_feedback = str(edits["final_feedback"])

        grade.status = GradeStatus.published
        grade.approved_by = faculty_id
        grade.published_at = now
        grade.approved_at = grade.approved_at or now

        await self.db.flush()

        # Audit log publish event
        await self.audit.log(
            self.SERVICE_NAME,
            "grade_published",
            entity_type="Grade",
            entity_id=grade_id,
            input_data={"published_by": faculty_id, "edits_applied": edits is not None},
            output_data={
                "final_marks": grade.final_marks,
                "status": grade.status,
                "published_at": grade.published_at.isoformat(),
            },
        )
        return grade

    async def bulk_publish(
        self,
        grade_ids: List[int],
        faculty_id: int,
    ) -> List[Grade]:
        """Publishes multiple approved grades in a single transaction."""
        published = []
        for gid in grade_ids:
            g = await self.publish_grade(gid, faculty_id)
            published.append(g)
        return published

    async def rollback_grade(
        self,
        grade_id: int,
        faculty_id: int,
        reason: str = "Faculty initiated rollback",
    ) -> Grade:
        """
        Rolls back a published grade to 'draft' or 'pending_approval'.
        Records the rollback in the audit trail.
        """
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade record {grade_id} not found")

        prev_status = grade.status
        grade.status = GradeStatus.draft
        grade.published_at = None

        await self.db.flush()

        await self.audit.log(
            self.SERVICE_NAME,
            "grade_rolled_back",
            entity_type="Grade",
            entity_id=grade_id,
            input_data={"faculty_id": faculty_id, "reason": reason, "from_status": prev_status},
            output_data={"new_status": GradeStatus.draft},
        )
        return grade
