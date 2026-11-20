import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.database import Submission, Assignment, Grade, User, get_db
from agents.submission_collection import SubmissionCollectionAgent
from runtime.audit import AuditLogger, new_run_id
from api.routes.auth import get_current_user, require_faculty

router = APIRouter(tags=["submissions"])


@router.post("/assignments/{assignment_id}/submit", status_code=201)
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can submit")

    file_bytes = await file.read()
    audit = AuditLogger(db, new_run_id(), current_user.id)
    agent = SubmissionCollectionAgent(db, audit)
    submission = await agent.collect(
        assignment_id=assignment_id,
        student_id=current_user.id,
        file_bytes=file_bytes,
        file_name=file.filename,
    )
    await db.commit()
    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "submitted_at": submission.submitted_at.isoformat(),
        "is_late": submission.is_late,
    }


@router.get("/assignments/{assignment_id}/submissions")
async def list_submissions(
    assignment_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.student), selectinload(Submission.grade))
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at)
    )
    subs = result.scalars().all()

    # Pre-fetch user map for resolving matched student IDs in similarity flags
    users_result = await db.execute(select(User))
    user_map = {u.id: u.name for u in users_result.scalars().all()}

    output = []
    for s in subs:
        raw_flags = json.loads(s.similarity_flags) if s.similarity_flags else []
        enriched_flags = []
        for f in raw_flags:
            f_item = dict(f)
            if "with_student" not in f_item:
                if "with_student_id" in f_item:
                    f_item["with_student"] = user_map.get(f_item["with_student_id"], f"Student #{f_item['with_student_id']}")
                elif "with_submission_id" in f_item:
                    f_item["with_student"] = f"Submission #{f_item['with_submission_id']}"
            enriched_flags.append(f_item)

        grade_info = None
        if s.grade:
            grade_info = {
                "id": s.grade.id,
                "draft_marks": s.grade.draft_marks,
                "final_marks": s.grade.final_marks,
                "status": s.grade.status,
                "draft_feedback": s.grade.draft_feedback,
                "final_feedback": s.grade.final_feedback,
                "rubric_breakdown": json.loads(s.grade.draft_rubric_breakdown) if s.grade.draft_rubric_breakdown else {},
            }

        output.append({
            "id": s.id,
            "student_id": s.student_id,
            "student_name": s.student.name if s.student else f"Student #{s.student_id}",
            "student_email": s.student.email if s.student else "",
            "submitted_at": s.submitted_at.isoformat(),
            "is_late": s.is_late,
            "file_name": s.file_name,
            "similarity_score": s.similarity_score,
            "similarity_flags": enriched_flags,
            "status": s.status,
            "grade": grade_info,
        })
    return output


@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.student), selectinload(Submission.grade))
        .where(Submission.id == submission_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {
        "id": s.id,
        "assignment_id": s.assignment_id,
        "student_id": s.student_id,
        "student_name": s.student.name if s.student else f"Student #{s.student_id}",
        "student_email": s.student.email if s.student else "",
        "submitted_at": s.submitted_at.isoformat(),
        "is_late": s.is_late,
        "file_name": s.file_name,
        "similarity_score": s.similarity_score,
        "similarity_flags": json.loads(s.similarity_flags) if s.similarity_flags else [],
    }


@router.get("/submissions/{submission_id}/download")
async def download_submission(submission_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    """Allows faculty to download the actual submitted file from the storage system."""
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    s = result.scalar_one_or_none()
    if not s or not s.file_path or not Path(s.file_path).exists():
        raise HTTPException(status_code=404, detail="Submission file not found on disk")

    return FileResponse(
        path=s.file_path,
        filename=s.file_name,
        media_type="application/octet-stream"
    )


@router.get("/submissions/{submission_id}/content")
async def get_submission_content(submission_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    """Provides file content and rubric evaluation for faculty in-app inspection."""
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.student), selectinload(Submission.assignment), selectinload(Submission.grade))
        .where(Submission.id == submission_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")

    content = ""
    p = Path(s.file_path) if s.file_path else None
    if p and p.exists():
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            try:
                from agents.grading_assistance import _extract_text
                content = _extract_text(str(p))
            except Exception as e:
                content = f"[Could not read file text: {e}]"
    else:
        content = "[File is stored in cloud repository or path unavailable]"

    grade_info = None
    if s.grade:
        grade_info = {
            "id": s.grade.id,
            "draft_marks": s.grade.draft_marks,
            "final_marks": s.grade.final_marks,
            "status": s.grade.status,
            "draft_feedback": s.grade.draft_feedback,
            "final_feedback": s.grade.final_feedback,
            "rubric_breakdown": json.loads(s.grade.draft_rubric_breakdown) if s.grade.draft_rubric_breakdown else {},
        }

    rubric = json.loads(s.assignment.rubric) if (s.assignment and s.assignment.rubric) else {}

    return {
        "id": s.id,
        "student_id": s.student_id,
        "student_name": s.student.name if s.student else f"Student #{s.student_id}",
        "student_email": s.student.email if s.student else "",
        "assignment_id": s.assignment_id,
        "assignment_title": s.assignment.title if s.assignment else "",
        "assignment_max_marks": s.assignment.max_marks if s.assignment else 100,
        "assignment_rubric": rubric,
        "file_name": s.file_name,
        "submitted_at": s.submitted_at.isoformat(),
        "is_late": s.is_late,
        "content": content,
        "similarity_score": s.similarity_score,
        "similarity_flags": json.loads(s.similarity_flags) if s.similarity_flags else [],
        "grade": grade_info,
    }
