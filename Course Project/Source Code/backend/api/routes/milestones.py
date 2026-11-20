from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from dateutil import parser as date_parser

from models.database import Milestone, MilestoneProgress, MilestoneProgressStatus, MilestoneHealth, ProjectGroup, GroupMember, User, ProjectFeedback, get_db
from agents.project_milestone import ProjectMilestoneAgent
from runtime.audit import AuditLogger, new_run_id
from api.routes.auth import get_current_user, require_faculty

router = APIRouter(prefix="/courses/{course_id}", tags=["milestones"])


class MilestoneCreate(BaseModel):
    title: str
    description: str = ""
    due_date: str
    checkpoint_number: int


class ApproveProgressRequest(BaseModel):
    group_id: int
    milestone_id: int


class FeedbackSubmitRequest(BaseModel):
    group_id: int
    milestone_id: Optional[int] = None
    category: str = "checkpoint"  # "checkpoint" or "github"
    feedback_text: str


def _parse_due_date(date_str: str) -> datetime:
    if not date_str or not date_str.strip():
        raise HTTPException(status_code=400, detail="Due date is required.")
    cleaned = date_str.strip()
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except Exception:
        try:
            return date_parser.parse(cleaned)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid date format: '{date_str}'. Please provide a valid ISO or standard date.")


@router.post("/milestones", status_code=201)
async def create_milestone(
    course_id: int,
    body: MilestoneCreate,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="Checkpoint title is required.")

    due_dt = _parse_due_date(body.due_date)

    ms = Milestone(
        course_id=course_id,
        title=body.title.strip(),
        description=body.description.strip(),
        due_date=due_dt,
        checkpoint_number=body.checkpoint_number,
    )
    db.add(ms)
    await db.flush()

    groups_result = await db.execute(select(ProjectGroup).where(ProjectGroup.course_id == course_id))
    groups = groups_result.scalars().all()
    for g in groups:
        db.add(MilestoneProgress(
            milestone_id=ms.id,
            group_id=g.id,
            status=MilestoneProgressStatus.not_started,
            health=MilestoneHealth.green,
        ))
    await db.commit()
    await db.refresh(ms)
    return {"id": ms.id, "title": ms.title, "checkpoint_number": ms.checkpoint_number, "due_date": ms.due_date.isoformat()}


@router.delete("/milestones/{milestone_id}")
async def delete_milestone(
    course_id: int,
    milestone_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id, Milestone.course_id == course_id)
    )
    ms = result.scalar_one_or_none()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # Delete associated progress records first
    await db.execute(delete(MilestoneProgress).where(MilestoneProgress.milestone_id == milestone_id))
    await db.delete(ms)
    await db.commit()
    return {"deleted": True, "milestone_id": milestone_id}


@router.get("/milestones")
async def list_milestones(course_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Milestone).where(Milestone.course_id == course_id).order_by(Milestone.checkpoint_number))
    milestones = result.scalars().all()
    return [
        {"id": m.id, "title": m.title, "description": m.description,
         "due_date": m.due_date.isoformat(), "checkpoint_number": m.checkpoint_number}
        for m in milestones
    ]


@router.get("/milestones/summary")
async def milestone_summary(course_id: int, db: AsyncSession = Depends(get_db), faculty=Depends(require_faculty)):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = ProjectMilestoneAgent(db, audit)
    return await agent.get_course_summary(course_id)


@router.get("/milestones/my-summary")
async def my_milestone_summary(course_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Student-specific endpoint: returns milestone progress only for the student's own team in this course."""
    # Find the student's group in this course
    result = await db.execute(
        select(GroupMember.group_id).join(ProjectGroup, ProjectGroup.id == GroupMember.group_id)
        .where(ProjectGroup.course_id == course_id, GroupMember.student_id == current_user.id)
    )
    row = result.first()
    if not row:
        return {"group": None, "milestones": []}

    student_group_id = row[0]

    # Get the group details including members
    group_result = await db.execute(select(ProjectGroup).where(ProjectGroup.id == student_group_id))
    group = group_result.scalar_one_or_none()

    # Get team member names
    members_result = await db.execute(
        select(User.name).join(GroupMember, GroupMember.student_id == User.id)
        .where(GroupMember.group_id == student_group_id)
    )
    member_names = [r[0] for r in members_result.all()]

    # Get all milestones for this course
    milestones_result = await db.execute(
        select(Milestone).where(Milestone.course_id == course_id).order_by(Milestone.checkpoint_number)
    )
    milestones = milestones_result.scalars().all()

    # Load all feedback records for student's group
    fb_result = await db.execute(
        select(ProjectFeedback, User.name)
        .join(User, User.id == ProjectFeedback.faculty_id)
        .where(ProjectFeedback.course_id == course_id, ProjectFeedback.group_id == student_group_id)
    )
    fb_rows = fb_result.all()
    feedback_map = {}
    for fb, fac_name in fb_rows:
        key = (fb.milestone_id, fb.category)
        feedback_map[key] = {
            "id": fb.id,
            "feedback_text": fb.feedback_text,
            "category": fb.category,
            "faculty_id": fb.faculty_id,
            "faculty_name": fac_name,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
            "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
        }

    # Build summary with only this student's group progress
    summary = []
    for ms in milestones:
        prog_result = await db.execute(
            select(MilestoneProgress).where(
                MilestoneProgress.milestone_id == ms.id,
                MilestoneProgress.group_id == student_group_id
            )
        )
        prog = prog_result.scalar_one_or_none()
        cp_fb = feedback_map.get((ms.id, "checkpoint"))
        gh_fb = feedback_map.get((ms.id, "github")) or feedback_map.get((None, "github"))
        summary.append({
            "milestone_id": ms.id,
            "milestone_title": ms.title,
            "checkpoint_number": ms.checkpoint_number,
            "due_date": ms.due_date.isoformat(),
            "group_id": student_group_id,
            "group_name": group.name if group else "Unknown",
            "status": prog.status if prog else "not_started",
            "health": prog.health if prog else "green",
            "notes": prog.notes if prog else None,
            "github_url": prog.github_url if prog else (group.github_url if group else None),
            "submission_file": prog.submission_file if prog else None,
            "submitted_at": prog.submitted_at.isoformat() if prog and prog.submitted_at else None,
            "checkpoint_feedback": cp_fb,
            "github_feedback": gh_fb,
        })

    return {
        "group": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "github_url": group.github_url,
            "members": member_names,
            "github_feedback": feedback_map.get((None, "github")),
        },
        "milestones": summary,
    }


@router.post("/milestones/{milestone_id}/submit")
async def submit_milestone_progress(
    course_id: int,
    milestone_id: int,
    group_id: int = Form(...),
    notes: str = Form(""),
    github_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read() if file else None
    file_name = file.filename if file else None
    audit = AuditLogger(db, new_run_id(), current_user.id)
    agent = ProjectMilestoneAgent(db, audit)
    prog = await agent.submit_progress(milestone_id, group_id, notes, file_bytes, file_name, github_url=github_url)
    await db.commit()
    return {"id": prog.id, "status": prog.status, "health": prog.health, "github_url": prog.github_url}


@router.post("/milestones/{milestone_id}/approve-group")
async def approve_group_progress(
    course_id: int,
    milestone_id: int,
    body: ApproveProgressRequest,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MilestoneProgress).where(
            MilestoneProgress.milestone_id == milestone_id,
            MilestoneProgress.group_id == body.group_id,
        )
    )
    prog = result.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=404, detail="Progress record not found")
    prog.status = MilestoneProgressStatus.approved
    from models.database import MilestoneHealth
    prog.health = MilestoneHealth.green
    await db.commit()
    return {"status": prog.status, "health": prog.health}


@router.post("/feedback")
@router.post("/milestones/feedback")
async def submit_or_update_feedback(
    course_id: int,
    body: FeedbackSubmitRequest,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    """Faculty endpoint to submit or edit feedback on a team checkpoint or GitHub submission."""
    if not body.feedback_text or not body.feedback_text.strip():
        raise HTTPException(status_code=400, detail="Feedback text cannot be empty.")

    # Verify group belongs to course
    g_res = await db.execute(
        select(ProjectGroup).where(ProjectGroup.id == body.group_id, ProjectGroup.course_id == course_id)
    )
    group = g_res.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Project group not found in this course.")

    # If milestone_id is provided, verify it belongs to this course
    if body.milestone_id:
        m_res = await db.execute(
            select(Milestone).where(Milestone.id == body.milestone_id, Milestone.course_id == course_id)
        )
        ms = m_res.scalar_one_or_none()
        if not ms:
            raise HTTPException(status_code=404, detail="Milestone not found in this course.")

    category = body.category.lower().strip()
    if category not in ("checkpoint", "github"):
        category = "checkpoint"

    # Check if feedback already exists for this exact tuple
    q = select(ProjectFeedback).where(
        ProjectFeedback.course_id == course_id,
        ProjectFeedback.group_id == body.group_id,
        ProjectFeedback.milestone_id == body.milestone_id,
        ProjectFeedback.category == category,
    )
    res = await db.execute(q)
    existing = res.scalar_one_or_none()

    now = datetime.utcnow()
    if existing:
        existing.feedback_text = body.feedback_text.strip()
        existing.faculty_id = faculty.id
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)
        fb_record = existing
    else:
        fb_record = ProjectFeedback(
            course_id=course_id,
            group_id=body.group_id,
            milestone_id=body.milestone_id,
            category=category,
            feedback_text=body.feedback_text.strip(),
            faculty_id=faculty.id,
            created_at=now,
            updated_at=now,
        )
        db.add(fb_record)
        await db.commit()
        await db.refresh(fb_record)

    return {
        "id": fb_record.id,
        "course_id": fb_record.course_id,
        "group_id": fb_record.group_id,
        "milestone_id": fb_record.milestone_id,
        "category": fb_record.category,
        "feedback_text": fb_record.feedback_text,
        "faculty_id": fb_record.faculty_id,
        "faculty_name": faculty.name,
        "created_at": fb_record.created_at.isoformat(),
        "updated_at": fb_record.updated_at.isoformat(),
    }


@router.get("/feedback")
@router.get("/milestones/feedback")
async def get_feedback_list(
    course_id: int,
    milestone_id: Optional[int] = None,
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve feedback with strict permission filtering: students only see their own team's feedback."""
    q = (
        select(ProjectFeedback, User.name)
        .join(User, User.id == ProjectFeedback.faculty_id)
        .where(ProjectFeedback.course_id == course_id)
    )

    if current_user.role == "student":
        # Find student's team
        member_res = await db.execute(
            select(GroupMember.group_id)
            .join(ProjectGroup, ProjectGroup.id == GroupMember.group_id)
            .where(ProjectGroup.course_id == course_id, GroupMember.student_id == current_user.id)
        )
        row = member_res.first()
        if not row:
            return []
        student_group_id = row[0]
        q = q.where(ProjectFeedback.group_id == student_group_id)

    if milestone_id is not None:
        q = q.where(ProjectFeedback.milestone_id == milestone_id)
    if category is not None:
        q = q.where(ProjectFeedback.category == category.lower().strip())

    res = await db.execute(q)
    rows = res.all()
    return [
        {
            "id": fb.id,
            "course_id": fb.course_id,
            "group_id": fb.group_id,
            "milestone_id": fb.milestone_id,
            "category": fb.category,
            "feedback_text": fb.feedback_text,
            "faculty_id": fb.faculty_id,
            "faculty_name": fac_name,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
            "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
        }
        for fb, fac_name in rows
    ]
