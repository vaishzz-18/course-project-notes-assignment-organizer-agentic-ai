import json
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Grade, GradeStatus, Submission, Assignment, User, get_db
from agents.coordinator import AURACoordinator
from agents.grading_assistance import GradingAssistanceAgent
from agents.grade_publishing import GradePublishingAgent
from runtime.audit import AuditLogger, new_run_id
from runtime.governance import GovernanceEngine
from api.routes.auth import get_current_user, require_faculty

router = APIRouter(tags=["grades"])


class ApproveGradeRequest(BaseModel):
    final_marks: Optional[float] = None
    final_feedback: Optional[str] = None


class BulkApproveRequest(BaseModel):
    grade_ids: List[int]


class NLQueryRequest(BaseModel):
    question: str
    history: Optional[List[Dict[str, str]]] = None


@router.post("/courses/{course_id}/assignments/{assignment_id}/run-grading")
async def run_grading_pipeline(
    course_id: int,
    assignment_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the full AURA grading pipeline: similarity → AI grade → validate → queue."""
    coordinator = AURACoordinator(db, faculty.id)
    result = await coordinator.run_grading_pipeline(course_id, assignment_id)
    return result


@router.post("/submissions/{submission_id}/grade")
async def grade_single_submission(
    submission_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    """Grade a single submission on demand with full cross-plagiarism check."""
    coordinator = AURACoordinator(db, faculty.id)
    result = await coordinator.grade_single_submission(submission_id)
    return result


@router.get("/courses/{course_id}/grades/pending")
async def pending_grades(course_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    q = (
        select(Grade, Submission, Assignment, User)
        .join(Submission, Grade.submission_id == Submission.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(User, Submission.student_id == User.id)
        .where(Assignment.course_id == course_id)
        .where(Grade.status == GradeStatus.pending_approval)
    )
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "grade_id": g.id,
            "submission_id": g.submission_id,
            "student_id": s.student_id,
            "student_name": u.name,
            "student_email": u.email,
            "submission_file_name": s.file_name,
            "assignment_title": a.title,
            "draft_marks": g.draft_marks,
            "max_marks": a.max_marks,
            "draft_feedback": g.draft_feedback,
            "draft_rubric_breakdown": json.loads(g.draft_rubric_breakdown) if g.draft_rubric_breakdown else {},
            "similarity_score": s.similarity_score,
            "similarity_flags": json.loads(s.similarity_flags) if s.similarity_flags else [],
            "evidence_record": json.loads(g.evidence_record) if g.evidence_record else {},
        }
        for g, s, a, u in rows
    ]


@router.post("/grades/{grade_id}/approve")
async def approve_grade(
    grade_id: int,
    body: ApproveGradeRequest,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    governance = GovernanceEngine(db, audit)
    publisher = GradePublishingAgent(db, audit, governance)
    edits = {}
    if body.final_marks is not None:
        edits["marks"] = body.final_marks
    if body.final_feedback is not None:
        edits["feedback"] = body.final_feedback
    grade = await publisher.step(grade_id, faculty.id, edits or None)
    await db.commit()
    return {
        "id": grade.id,
        "status": grade.status,
        "final_marks": grade.final_marks,
        "published_at": grade.published_at.isoformat() if grade.published_at else None,
    }


@router.post("/grades/bulk-approve")
async def bulk_approve(body: BulkApproveRequest, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    governance = GovernanceEngine(db, audit)
    publisher = GradePublishingAgent(db, audit, governance)
    grades = await publisher.bulk_publish(body.grade_ids, faculty.id)
    await db.commit()
    return {"published": len(grades), "grade_ids": [g.id for g in grades]}


@router.post("/grades/{grade_id}/rollback")
async def rollback_grade(grade_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    governance = GovernanceEngine(db, audit)
    publisher = GradePublishingAgent(db, audit, governance)
    grade = await publisher.rollback(grade_id, faculty.id)
    await db.commit()
    return {"id": grade.id, "status": grade.status}


@router.post("/courses/{course_id}/query")
async def nl_query(course_id: int, body: NLQueryRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    audit = AuditLogger(db, new_run_id(), current_user.id)
    agent = GradingAssistanceAgent(db, audit)
    answer = await agent.nl_query(
        course_id,
        body.question,
        user_role=current_user.role,
        user_id=current_user.id,
        history=body.history,
    )
    return {"question": body.question, "answer": answer}


@router.get("/students/{student_id}/grades")
async def student_grades(student_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    q = (
        select(Grade, Submission, Assignment)
        .join(Submission, Grade.submission_id == Submission.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(Submission.student_id == student_id)
        .where(Grade.status == GradeStatus.published)
    )
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "assignment_title": a.title,
            "final_marks": g.final_marks,
            "max_marks": a.max_marks,
            "final_feedback": g.final_feedback,
            "published_at": g.published_at.isoformat() if g.published_at else None,
        }
        for g, s, a in rows
    ]
