from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.database import Course, CourseEnrollment, User, ProjectGroup, GroupMember, MilestoneProgress, get_db
from api.routes.auth import get_current_user, require_faculty

router = APIRouter(prefix="/courses", tags=["courses"])


class CourseCreate(BaseModel):
    name: str
    code: str
    description: str = ""


class EnrollRequest(BaseModel):
    student_ids: List[int]


class GroupCreate(BaseModel):
    name: str
    description: str = ""
    member_ids: List[int] = []


class UpdateEnrollmentsRequest(BaseModel):
    course_ids: List[int]


@router.post("", status_code=201)
async def create_course(body: CourseCreate, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    course = Course(name=body.name, code=body.code, description=body.description, faculty_id=faculty.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return {"id": course.id, "name": course.name, "code": course.code}


@router.get("")
async def list_courses(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role in ("faculty", "hod"):
        result = await db.execute(select(Course).where(Course.faculty_id == current_user.id))
    else:
        result = await db.execute(
            select(Course).join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
            .where(CourseEnrollment.student_id == current_user.id)
        )
    courses = result.scalars().all()
    return [{"id": c.id, "name": c.name, "code": c.code, "description": c.description, "faculty_id": c.faculty_id} for c in courses]


@router.get("/catalog/all")
async def get_course_catalog(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns the full curriculum course catalog with enrollment status for student/faculty."""
    result = await db.execute(select(Course).order_by(Course.code))
    all_courses = result.scalars().all()

    enrolled_ids = set()
    if current_user.role == "student":
        enr_res = await db.execute(
            select(CourseEnrollment.course_id).where(CourseEnrollment.student_id == current_user.id)
        )
        enrolled_ids = {r[0] for r in enr_res.all()}
    else:
        enrolled_ids = {c.id for c in all_courses if c.faculty_id == current_user.id}

    return [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "description": c.description,
            "is_enrolled": c.id in enrolled_ids,
        }
        for c in all_courses
    ]


@router.post("/my-enrollments")
async def update_my_enrollments(
    body: UpdateEnrollmentsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Allows student or faculty to update, add, or change their course enrollments for next semester/year."""
    if current_user.role == "student":
        # Remove current active enrollments
        await db.execute(
            delete(CourseEnrollment).where(CourseEnrollment.student_id == current_user.id)
        )
        # Add updated enrollments
        for cid in body.course_ids:
            c_check = await db.execute(select(Course).where(Course.id == cid))
            if c_check.scalar_one_or_none():
                db.add(CourseEnrollment(course_id=cid, student_id=current_user.id))
        await db.commit()

        res = await db.execute(
            select(Course).join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
            .where(CourseEnrollment.student_id == current_user.id)
        )
        updated_courses = res.scalars().all()
        return [{"id": c.id, "name": c.name, "code": c.code, "description": c.description} for c in updated_courses]
    else:
        # Faculty updating assigned courses
        for cid in body.course_ids:
            c_res = await db.execute(select(Course).where(Course.id == cid))
            course = c_res.scalar_one_or_none()
            if course:
                course.faculty_id = current_user.id
        await db.commit()
        res = await db.execute(select(Course).where(Course.faculty_id == current_user.id))
        updated_courses = res.scalars().all()
        return [{"id": c.id, "name": c.name, "code": c.code, "description": c.description} for c in updated_courses]


@router.get("/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"id": course.id, "name": course.name, "code": course.code, "description": course.description, "faculty_id": course.faculty_id}


@router.post("/{course_id}/enroll")
async def enroll_students(course_id: int, body: EnrollRequest, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    for sid in body.student_ids:
        existing = await db.execute(
            select(CourseEnrollment).where(CourseEnrollment.course_id == course_id, CourseEnrollment.student_id == sid)
        )
        if not existing.scalar_one_or_none():
            db.add(CourseEnrollment(course_id=course_id, student_id=sid))
    await db.commit()
    return {"enrolled": len(body.student_ids)}


@router.get("/{course_id}/students")
async def get_students(course_id: int, db: AsyncSession = Depends(get_db), faculty=Depends(require_faculty)):
    q = (select(User).join(CourseEnrollment, CourseEnrollment.student_id == User.id).where(CourseEnrollment.course_id == course_id))
    result = await db.execute(q)
    students = result.scalars().all()
    return [{"id": s.id, "name": s.name, "email": s.email} for s in students]


@router.post("/{course_id}/groups", status_code=201)
async def create_group(course_id: int, body: GroupCreate, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    from models.database import Milestone, MilestoneProgress, MilestoneProgressStatus, MilestoneHealth
    group = ProjectGroup(course_id=course_id, name=body.name, description=body.description)
    db.add(group)
    await db.flush()
    for mid in body.member_ids:
        db.add(GroupMember(group_id=group.id, student_id=mid))

    # Link new group with all existing milestones in this course
    ms_result = await db.execute(select(Milestone).where(Milestone.course_id == course_id))
    milestones = ms_result.scalars().all()
    for ms in milestones:
        db.add(MilestoneProgress(
            milestone_id=ms.id,
            group_id=group.id,
            status=MilestoneProgressStatus.not_started,
            health=MilestoneHealth.green,
        ))

    await db.commit()
    await db.refresh(group)
    return {"id": group.id, "name": group.name}


@router.get("/{course_id}/groups")
async def list_groups(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectGroup).where(ProjectGroup.course_id == course_id))
    groups = result.scalars().all()
    group_list = []
    for g in groups:
        members_res = await db.execute(
            select(User.name).join(GroupMember, GroupMember.student_id == User.id)
            .where(GroupMember.group_id == g.id)
        )
        member_names = [r[0] for r in members_res.all()]

        # Resolve github_url from group or latest milestone progress
        github_url = g.github_url
        if not github_url:
            mp_res = await db.execute(
                select(MilestoneProgress.github_url)
                .where(MilestoneProgress.group_id == g.id, MilestoneProgress.github_url.isnot(None))
                .order_by(MilestoneProgress.id.desc())
            )
            github_url = mp_res.scalars().first()

        group_list.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "github_url": github_url,
            "members": member_names,
        })
    return group_list
