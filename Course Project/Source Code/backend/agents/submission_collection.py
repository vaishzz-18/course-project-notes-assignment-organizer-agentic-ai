"""Submission Collection Agent — gathers submissions and timestamps against deadline."""
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Submission, Assignment
from runtime.audit import AuditLogger
from config import settings


class SubmissionCollectionAgent:
    AGENT_NAME = "SubmissionCollectionAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def collect(
        self,
        assignment_id: int,
        student_id: int,
        file_bytes: bytes,
        file_name: str,
    ) -> Submission:
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        now = datetime.utcnow()
        is_late = now > assignment.due_date

        dest_dir = settings.SUBMISSIONS_DIR / str(assignment_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        ts = now.strftime("%Y%m%d_%H%M%S")
        safe_name = f"student_{student_id}_{ts}_{file_name}"
        dest_path = dest_dir / safe_name
        dest_path.write_bytes(file_bytes)

        existing = await self.db.execute(
            select(Submission).where(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
        )
        old_sub = existing.scalar_one_or_none()
        if old_sub:
            old_sub.file_path = str(dest_path)
            old_sub.file_name = file_name
            old_sub.submitted_at = now
            old_sub.is_late = is_late
            old_sub.status = "submitted"
            submission = old_sub
        else:
            submission = Submission(
                assignment_id=assignment_id,
                student_id=student_id,
                file_path=str(dest_path),
                file_name=file_name,
                submitted_at=now,
                is_late=is_late,
                status="submitted",
            )
            self.db.add(submission)

        await self.db.flush()

        await self.audit.log(
            self.AGENT_NAME, "submission_collected",
            entity_type="Submission", entity_id=submission.id,
            input_data={"assignment_id": assignment_id, "student_id": student_id},
            output_data={"submitted_at": now.isoformat(), "is_late": is_late},
        )
        return submission

    async def step(self, submission: Submission, due_date: datetime):
        """Pipeline step: ensure timestamp and late flag are set."""
        if submission.submitted_at and submission.is_late is None:
            submission.is_late = submission.submitted_at > due_date
            await self.db.flush()
