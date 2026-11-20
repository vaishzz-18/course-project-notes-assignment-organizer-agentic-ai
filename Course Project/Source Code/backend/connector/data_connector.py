"""
MCP-style data connector — the single governed surface for all data access.
No agent touches a data source directly; all access goes through here.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.database import (
    Note, Assignment, Submission, Grade, Milestone,
    MilestoneProgress, ProjectGroup, CourseEnrollment, User
)


class DataConnector:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Notes / Materials store ───────────────────────────────────────────────

    async def read_notes(self, course_id: int, unit: Optional[str] = None) -> List[Note]:
        q = select(Note).where(Note.course_id == course_id, Note.is_current == True)
        if unit:
            q = q.where(Note.unit == unit)
        result = await self.db.execute(q.order_by(Note.unit, Note.topic))
        return result.scalars().all()

    async def read_note_versions(self, note_id: int) -> List[Note]:
        result = await self.db.execute(
            select(Note).where(Note.parent_id == note_id).order_by(Note.version)
        )
        return result.scalars().all()

    # ── Assignment & rubric definitions ──────────────────────────────────────

    async def read_assignments(self, course_id: int, status: Optional[str] = None) -> List[Assignment]:
        q = select(Assignment).where(Assignment.course_id == course_id)
        if status:
            q = q.where(Assignment.status == status)
        result = await self.db.execute(q.order_by(Assignment.due_date))
        return result.scalars().all()

    async def read_assignment(self, assignment_id: int) -> Optional[Assignment]:
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        return result.scalar_one_or_none()

    # ── Submission records ────────────────────────────────────────────────────

    async def read_submissions(
        self,
        assignment_id: Optional[int] = None,
        student_id: Optional[int] = None,
    ) -> List[Submission]:
        q = select(Submission)
        if assignment_id:
            q = q.where(Submission.assignment_id == assignment_id)
        if student_id:
            q = q.where(Submission.student_id == student_id)
        result = await self.db.execute(q.order_by(Submission.submitted_at))
        return result.scalars().all()

    async def read_submission(self, submission_id: int) -> Optional[Submission]:
        result = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        return result.scalar_one_or_none()

    # ── Grades ────────────────────────────────────────────────────────────────

    async def read_grade(self, submission_id: int) -> Optional[Grade]:
        result = await self.db.execute(select(Grade).where(Grade.submission_id == submission_id))
        return result.scalar_one_or_none()

    async def read_pending_grades(self, course_id: int) -> List[Grade]:
        q = (
            select(Grade)
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Assignment.course_id == course_id)
            .where(Grade.status == "pending_approval")
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    # ── Milestones ────────────────────────────────────────────────────────────

    async def read_milestones(self, course_id: int) -> List[Milestone]:
        result = await self.db.execute(
            select(Milestone)
            .where(Milestone.course_id == course_id)
            .order_by(Milestone.checkpoint_number)
        )
        return result.scalars().all()

    async def read_milestone_progress(self, milestone_id: int) -> List[MilestoneProgress]:
        result = await self.db.execute(
            select(MilestoneProgress).where(MilestoneProgress.milestone_id == milestone_id)
        )
        return result.scalars().all()

    # ── Enrollment ────────────────────────────────────────────────────────────

    async def read_enrolled_students(self, course_id: int) -> List[User]:
        q = (
            select(User)
            .join(CourseEnrollment, CourseEnrollment.student_id == User.id)
            .where(CourseEnrollment.course_id == course_id)
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    async def read_project_groups(self, course_id: int) -> List[ProjectGroup]:
        result = await self.db.execute(
            select(ProjectGroup).where(ProjectGroup.course_id == course_id)
        )
        return result.scalars().all()
