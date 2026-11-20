"""Assignment Distribution Agent — releases assignments on schedule, sends deadline reminders."""
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.database import Assignment, AssignmentStatus, CourseEnrollment, User
from runtime.audit import AuditLogger


class AssignmentDistributionAgent:
    AGENT_NAME = "AssignmentDistributionAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def publish_assignment(self, assignment_id: int, faculty_id: int) -> Assignment:
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        if assignment.status != AssignmentStatus.draft:
            raise ValueError("Only draft assignments can be published")

        assignment.status = AssignmentStatus.published
        assignment.published_at = datetime.utcnow()
        await self.db.flush()

        students = await self._get_enrolled_students(assignment.course_id)
        notifications = self._build_notifications(assignment, students)

        await self.audit.log(
            self.AGENT_NAME, "assignment_published",
            entity_type="Assignment", entity_id=assignment_id,
            input_data={"faculty_id": faculty_id},
            output_data={
                "published_at": assignment.published_at.isoformat(),
                "notified_students": len(students),
            },
        )
        return assignment

    async def close_assignment(self, assignment_id: int) -> Assignment:
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        assignment.status = AssignmentStatus.closed
        await self.db.flush()
        await self.audit.log(
            self.AGENT_NAME, "assignment_closed",
            entity_type="Assignment", entity_id=assignment_id,
        )
        return assignment

    async def get_deadline_reminders(self, course_id: int) -> List[dict]:
        """Return students who haven't submitted for each published assignment."""
        from models.database import Submission
        result = await self.db.execute(
            select(Assignment).where(
                Assignment.course_id == course_id,
                Assignment.status == AssignmentStatus.published,
            )
        )
        assignments = result.scalars().all()

        reminders = []
        for assignment in assignments:
            students = await self._get_enrolled_students(course_id)
            result2 = await self.db.execute(
                select(Submission.student_id).where(Submission.assignment_id == assignment.id)
            )
            submitted_ids = {r[0] for r in result2.all()}
            pending = [s for s in students if s.id not in submitted_ids]
            if pending:
                reminders.append({
                    "assignment_id": assignment.id,
                    "assignment_title": assignment.title,
                    "due_date": assignment.due_date.isoformat(),
                    "pending_students": [{"id": s.id, "name": s.name, "email": s.email} for s in pending],
                })
        return reminders

    async def _get_enrolled_students(self, course_id: int) -> List[User]:
        q = (
            select(User)
            .join(CourseEnrollment, CourseEnrollment.student_id == User.id)
            .where(CourseEnrollment.course_id == course_id)
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    def _build_notifications(self, assignment: Assignment, students: List[User]) -> List[dict]:
        return [
            {
                "to": s.email,
                "subject": f"[{assignment.course_id}] New Assignment: {assignment.title}",
                "body": f"Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}",
            }
            for s in students
        ]
