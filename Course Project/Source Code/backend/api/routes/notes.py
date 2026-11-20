from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from datetime import datetime

from models.database import Note, Course, LessonPlan, CourseUnit, CourseChapter, CourseTopic, CourseLesson, get_db
from agents.notes_repository import NotesRepositoryAgent
from runtime.audit import AuditLogger, new_run_id
from api.routes.auth import get_current_user, require_faculty
from config import settings
from services.retrieval_service import RetrievalService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/courses/{course_id}/notes", status_code=201)
async def upload_note(
    course_id: int,
    title: str = Form(...),
    unit: str = Form(...),
    topic: str = Form(...),
    file: UploadFile = File(...),
    replace_note_id: Optional[int] = Form(None),
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = NotesRepositoryAgent(db, audit)
    note = await agent.upload_note(
        course_id=course_id,
        title=title,
        unit=unit,
        topic=topic,
        file_bytes=file_bytes,
        file_name=file.filename,
        uploaded_by=faculty.id,
        replace_note_id=replace_note_id,
    )
    await db.commit()
    return {
        "id": note.id, "title": note.title, "unit": note.unit,
        "topic": note.topic, "version": note.version, "is_current": note.is_current,
        "file_name": note.file_name, "created_at": note.created_at.isoformat(),
    }


@router.get("/courses/{course_id}/notes")
async def list_notes(
    course_id: int,
    unit: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(Note).where(Note.course_id == course_id, Note.is_current == True)
    if unit:
        q = q.where(Note.unit == unit)
    result = await db.execute(q.order_by(Note.unit, Note.topic))
    notes = result.scalars().all()
    return [
        {
            "id": n.id, "title": n.title, "unit": n.unit, "topic": n.topic,
            "version": n.version, "file_name": n.file_name,
            "created_at": n.created_at.isoformat(), "uploaded_by": n.uploaded_by,
        }
        for n in notes
    ]


@router.get("/courses/{course_id}/search")
@router.get("/courses/{course_id}/notes/search")
async def search_notes(
    course_id: int,
    q: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Semantic vector search across indexed course note chunks."""
    retrieval_svc = RetrievalService()
    results = await retrieval_svc.search(db, query=q, course_id=course_id, top_k=top_k)
    return {
        "status": "success",
        "course_id": course_id,
        "query": q,
        "total_results": len(results),
        "results": results,
    }


@router.post("/courses/{course_id}/index-notes")
async def index_course_notes(
    course_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    """Indexes text from all current course notes into vector chunks."""
    retrieval_svc = RetrievalService()
    q = select(Note).where(Note.course_id == course_id, Note.is_current == True)
    res = await db.execute(q)
    notes = res.scalars().all()

    indexed_notes = 0
    total_chunks = 0

    for note in notes:
        text = ""
        file_p = Path(note.file_path)
        if file_p.exists():
            try:
                if file_p.suffix.lower() == ".pdf":
                    import fitz
                    doc = fitz.open(str(file_p))
                    text = " ".join(page.get_text() for page in doc)
                else:
                    text = file_p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
        if not text:
            text = f"{note.title}\n{note.unit}\n{note.topic}"

        chunks = await retrieval_svc.index_note(db, note.id, course_id, text)
        if chunks > 0:
            indexed_notes += 1
            total_chunks += chunks

    await db.commit()
    return {
        "status": "success",
        "course_id": course_id,
        "indexed_notes": indexed_notes,
        "total_chunks": total_chunks,
    }


@router.get("/notes/{note_id}/download")
async def download_note(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    path = Path(note.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(path), filename=note.file_name)


@router.get("/notes/{note_id}/versions")
async def note_versions(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    audit = AuditLogger(db, new_run_id(), current_user.id)
    agent = NotesRepositoryAgent(db, audit)
    versions = await agent.list_versions(note_id)
    return [{"id": v.id, "version": v.version, "created_at": v.created_at.isoformat(), "file_name": v.file_name} for v in versions]


@router.post("/notes/{note_id}/restore")
async def restore_note_version(note_id: int, faculty=Depends(require_faculty), db: AsyncSession = Depends(get_db)):
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = NotesRepositoryAgent(db, audit)
    note = await agent.restore_version(note_id, faculty.id)
    await db.commit()
    return {"id": note.id, "version": note.version, "is_current": True}


# ── Course-Level Curriculum & Lesson Plan Endpoints ─────────────────────────

@router.get("/courses/{course_id}/curriculum")
async def get_course_curriculum(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lp_res = await db.execute(select(LessonPlan).where(LessonPlan.course_id == course_id))
    lp = lp_res.scalar_one_or_none()
    lp_data = None
    if lp:
        lp_data = {
            "id": lp.id,
            "file_name": lp.file_name,
            "uploaded_at": lp.uploaded_at.isoformat() if lp.uploaded_at else None,
            "download_url": f"/api/notes/courses/{course_id}/lesson-plan/download",
        }

    units_res = await db.execute(
        select(CourseUnit)
        .where(CourseUnit.course_id == course_id)
        .order_by(CourseUnit.unit_number)
    )
    units = units_res.scalars().all()

    units_data = []
    for u in units:
        chapters_res = await db.execute(
            select(CourseChapter)
            .where(CourseChapter.unit_id == u.id)
            .order_by(CourseChapter.chapter_number)
        )
        chapters = chapters_res.scalars().all()
        chapters_data = []
        for ch in chapters:
            # 1. Fetch topics covered under this chapter
            topics_res = await db.execute(
                select(CourseTopic)
                .where(CourseTopic.chapter_id == ch.id)
                .order_by(CourseTopic.topic_number)
            )
            topics = topics_res.scalars().all()
            topics_data = [
                {
                    "id": t.id,
                    "topic_number": t.topic_number,
                    "title": t.title,
                }
                for t in topics
            ]

            # 2. Fetch chapter-level documents/notes
            notes_res = await db.execute(
                select(Note)
                .where(Note.chapter_id == ch.id, Note.is_current == True)
                .order_by(Note.created_at)
            )
            notes = notes_res.scalars().all()
            notes_data = [
                {
                    "id": n.id,
                    "title": n.title,
                    "file_name": n.file_name,
                    "version": n.version,
                    "uploaded_by": n.uploaded_by,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notes
            ]

            chapters_data.append({
                "id": ch.id,
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "topics": topics_data,
                "notes": notes_data,
            })
        units_data.append({
            "id": u.id,
            "unit_number": u.unit_number,
            "title": u.title,
            "chapters": chapters_data,
        })

    return {
        "course_id": course.id,
        "course_name": course.name,
        "course_code": course.code,
        "faculty_id": course.faculty_id,
        "lesson_plan": lp_data,
        "units": units_data,
    }


@router.post("/courses/{course_id}/lesson-plan", status_code=201)
async def upload_lesson_plan(
    course_id: int,
    file: UploadFile = File(...),
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.faculty_id != faculty.id and faculty.role != "hod":
        raise HTTPException(status_code=403, detail="Only assigned faculty can upload Lesson Plan for this course")

    dest_dir = settings.NOTES_DIR / str(course_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"LP_{ts}_{file.filename}"
    dest_path = dest_dir / safe_name
    file_bytes = await file.read()
    dest_path.write_bytes(file_bytes)

    lp_res = await db.execute(select(LessonPlan).where(LessonPlan.course_id == course_id))
    lp = lp_res.scalar_one_or_none()
    if lp:
        lp.file_path = str(dest_path)
        lp.file_name = file.filename
        lp.uploaded_by = faculty.id
        lp.uploaded_at = datetime.utcnow()
    else:
        lp = LessonPlan(
            course_id=course_id,
            file_path=str(dest_path),
            file_name=file.filename,
            uploaded_by=faculty.id,
            uploaded_at=datetime.utcnow(),
        )
        db.add(lp)
    await db.commit()
    await db.refresh(lp)
    return {
        "id": lp.id,
        "file_name": lp.file_name,
        "uploaded_at": lp.uploaded_at.isoformat() if lp.uploaded_at else None,
    }


@router.get("/courses/{course_id}/lesson-plan/download")
async def download_lesson_plan(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    lp_res = await db.execute(select(LessonPlan).where(LessonPlan.course_id == course_id))
    lp = lp_res.scalar_one_or_none()
    if not lp:
        raise HTTPException(status_code=404, detail="Lesson Plan not found for this course")
    path = Path(lp.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Lesson Plan file not found on disk")
    return FileResponse(str(path), filename=lp.file_name)


@router.post("/courses/{course_id}/lessons/{lesson_id}/notes", status_code=201)
async def upload_lesson_note(
    course_id: int,
    lesson_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.faculty_id != faculty.id and faculty.role != "hod":
        raise HTTPException(status_code=403, detail="Only assigned faculty can upload notes for this course")

    les_res = await db.execute(select(CourseLesson).where(CourseLesson.id == lesson_id))
    lesson = les_res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    ch_res = await db.execute(select(CourseChapter).where(CourseChapter.id == lesson.chapter_id))
    chapter = ch_res.scalar_one_or_none()
    unit_title = "Unit 1"
    if chapter:
        u_res = await db.execute(select(CourseUnit).where(CourseUnit.id == chapter.unit_id))
        unit = u_res.scalar_one_or_none()
        if unit:
            unit_title = unit.title

    note_title = title.strip() if title and title.strip() else file.filename
    file_bytes = await file.read()
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = NotesRepositoryAgent(db, audit)
    note = await agent.upload_note(
        course_id=course_id,
        title=note_title,
        unit=unit_title,
        topic=lesson.title,
        file_bytes=file_bytes,
        file_name=file.filename,
        uploaded_by=faculty.id,
        lesson_id=lesson.id,
    )
    await db.commit()
    return {
        "id": note.id,
        "title": note.title,
        "unit": note.unit,
        "topic": note.topic,
        "version": note.version,
        "file_name": note.file_name,
        "lesson_id": note.lesson_id,
        "created_at": note.created_at.isoformat(),
    }


@router.post("/courses/{course_id}/chapters/{chapter_id}/notes", status_code=201)
async def upload_chapter_note(
    course_id: int,
    chapter_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    course_res = await db.execute(select(Course).where(Course.id == course_id))
    course = course_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.faculty_id != faculty.id and faculty.role != "hod":
        raise HTTPException(status_code=403, detail="Only assigned faculty can upload notes for this course")

    ch_res = await db.execute(select(CourseChapter).where(CourseChapter.id == chapter_id))
    chapter = ch_res.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    u_res = await db.execute(select(CourseUnit).where(CourseUnit.id == chapter.unit_id))
    unit = u_res.scalar_one_or_none()
    unit_title = unit.title if unit else "Unit 1"

    note_title = title.strip() if title and title.strip() else file.filename
    file_bytes = await file.read()
    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = NotesRepositoryAgent(db, audit)
    note = await agent.upload_note(
        course_id=course_id,
        title=note_title,
        unit=unit_title,
        topic=chapter.title,
        file_bytes=file_bytes,
        file_name=file.filename,
        uploaded_by=faculty.id,
        chapter_id=chapter.id,
    )
    await db.commit()
    return {
        "id": note.id,
        "title": note.title,
        "unit": note.unit,
        "topic": note.topic,
        "version": note.version,
        "file_name": note.file_name,
        "chapter_id": note.chapter_id,
        "created_at": note.created_at.isoformat(),
    }


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    faculty=Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Note).where(Note.id == note_id))
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    c_res = await db.execute(select(Course).where(Course.id == note.course_id))
    course = c_res.scalar_one_or_none()
    if course and course.faculty_id != faculty.id and faculty.role != "hod":
        raise HTTPException(status_code=403, detail="Only assigned faculty can delete notes from this course")

    audit = AuditLogger(db, new_run_id(), faculty.id)
    agent = NotesRepositoryAgent(db, audit)
    await agent.delete_note(note_id, faculty.id)
    await db.commit()
    return {"message": "Document deleted successfully", "note_id": note_id}
