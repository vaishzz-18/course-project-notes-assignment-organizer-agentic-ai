"""
FacultyApprovalService — Governed human-in-the-loop approval workflow.
Manages the transitions:
  DRAFT -> PENDING_APPROVAL -> APPROVED / EDITED / REJECTED -> PUBLISHED
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Grade, GradeStatus, Submission, Assignment
from runtime.audit import AuditLogger


class FacultyApprovalService:
    SERVICE_NAME = "FacultyApprovalService"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def submit_for_review(
        self,
        grade_id: int,
        submitted_by_agent: str = "AURAOrchestrator",
    ) -> Grade:
        """Transitions an AI-drafted grade to PENDING_FACULTY_REVIEW."""
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade {grade_id} not found")

        grade.status = GradeStatus.pending_approval
        await self.db.flush()

        await self.audit.log(
            self.SERVICE_NAME,
            "submitted_for_review",
            entity_type="Grade",
            entity_id=grade_id,
            input_data={"submitted_by": submitted_by_agent},
            output_data={"status": GradeStatus.pending_approval},
        )
        return grade

    async def approve_grade(
        self,
        grade_id: int,
        faculty_id: int,
        edits: Optional[Dict[str, Any]] = None,
    ) -> Grade:
        """Faculty explicitly approves the draft grade (with optional manual overrides)."""
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade {grade_id} not found")

        now = datetime.now(timezone.utc)
        grade.status = GradeStatus.approved
        grade.approved_by = faculty_id
        grade.approved_at = now

        if edits:
            if "final_marks" in edits and edits["final_marks"] is not None:
                grade.final_marks = float(edits["final_marks"])
            if "final_feedback" in edits and edits["final_feedback"] is not None:
                grade.final_feedback = str(edits["final_feedback"])

        await self.db.flush()

        await self.audit.log(
            self.SERVICE_NAME,
            "grade_approved_by_faculty",
            entity_type="Grade",
            entity_id=grade_id,
            input_data={"faculty_id": faculty_id, "edits": edits},
            output_data={
                "status": grade.status,
                "approved_by": faculty_id,
                "final_marks": grade.final_marks,
            },
        )
        return grade

    async def reject_grade(
        self,
        grade_id: int,
        faculty_id: int,
        reason: str,
    ) -> Grade:
        """Faculty rejects the AI draft, requesting re-evaluation or manual override."""
        result = await self.db.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()
        if not grade:
            raise ValueError(f"Grade {grade_id} not found")

        grade.status = GradeStatus.draft
        await self.db.flush()

        await self.audit.log(
            self.SERVICE_NAME,
            "grade_rejected_by_faculty",
            entity_type="Grade",
            entity_id=grade_id,
            input_data={"faculty_id": faculty_id, "reason": reason},
            output_data={"new_status": GradeStatus.draft},
        )
        return grade

    async def get_pending_approvals(
        self,
        course_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves all grades waiting in the human approval queue."""
        q = (
            select(Grade, Submission, Assignment)
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Grade.status == GradeStatus.pending_approval)
        )
        if assignment_id:
            q = q.where(Submission.assignment_id == assignment_id)
        if course_id:
            q = q.where(Assignment.course_id == course_id)

        result = await self.db.execute(q)
        rows = result.all()

        return [
            {
                "grade_id": g.id,
                "submission_id": s.id,
                "assignment_id": a.id,
                "assignment_title": a.title,
                "student_id": s.student_id,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "is_late": s.is_late,
                "similarity_score": s.similarity_score,
                "draft_marks": g.draft_marks,
                "draft_feedback": g.draft_feedback,
                "rubric_breakdown": g.rubric_breakdown,
                "status": g.status,
            }
            for g, s, a in rows
        ]
