import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import Assignment, AssignmentStatus, get_db
from agents.assignment_distribution import AssignmentDistributionAgent
from runtime.audit import AuditLogger, new_run_id
from api.routes.auth import get_current_user, require_faculty

router = APIRouter(prefix="/courses/{course_id}", tags=["assignments"])


class AssignmentCreate(BaseModel):
    title: str
    description: str
    rubric: dict
    max_marks: float
    due_date: str  # ISO format


@router.post("/assignments", status_code=201)
async def create_assignment(
    course_id: int,
    body: AssignmentCreate,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    due = datetime.fromisoformat(body.due_date)
    assignment = Assignment(
        course_id=course_id,
        title=body.title,
        description=body.description,
        rubric=json.dumps(body.rubric),
        max_marks=body.max_marks,
        due_date=due,
        status=AssignmentStatus.draft,
        created_by=faculty.id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return {
        "id": assignment.id, "title": assignment.title,
        "max_marks": assignment.max_marks, "due_date": assignment.due_date.isoformat(),
        "status": assignment.status,
    }


@router.get("/assignments")
async def list_assignments(
    course_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(Assignment).where(Assignment.course_id == course_id)
    if status:
        q = q.where(Assignment.status == status)
    if current_user.role == "student":
        q = q.where(Assignment.status == AssignmentStatus.published)
    result = await db.execute(q.order_by(Assignment.due_date))
    assignments = result.scalars().all()
    return [
        {
            "id": a.id, "title": a.title, "description": a.description,
            "max_marks": a.max_marks, "due_date": a.due_date.isoformat(),
            "status": a.status, "rubric": json.loads(a.rubric) if a.rubric else {},
        }
        for a in assignments
    ]


@router.post("/assignments/{assignment_id}/publish")
async def publish_assignment(
    course_id: int,
    assignment_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = AssignmentDistributionAgent(db, audit)
    assignment = await agent.publish_assignment(assignment_id, faculty.id)
    await db.commit()
    return {"id": assignment.id, "status": assignment.status, "published_at": assignment.published_at.isoformat()}


@router.post("/assignments/{assignment_id}/close")
async def close_assignment(
    course_id: int,
    assignment_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = AssignmentDistributionAgent(db, audit)
    assignment = await agent.close_assignment(assignment_id)
    await db.commit()
    return {"id": assignment.id, "status": assignment.status}


@router.get("/reminders")
async def get_reminders(course_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = AssignmentDistributionAgent(db, audit)
    return await agent.get_deadline_reminders(course_id)
