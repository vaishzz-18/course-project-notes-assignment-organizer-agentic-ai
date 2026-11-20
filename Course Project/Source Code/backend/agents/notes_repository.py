"""Notes Repository Agent — maintains one current, versioned set of materials."""
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.database import Note
from runtime.audit import AuditLogger
from validation.validator import validate_notes_upload
from config import settings


class NotesRepositoryAgent:
    AGENT_NAME = "NotesRepositoryAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def upload_note(
        self,
        course_id: int,
        title: str,
        unit: str,
        topic: str,
        file_bytes: bytes,
        file_name: str,
        uploaded_by: int,
        replace_note_id: Optional[int] = None,
        lesson_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
    ) -> Note:
        dest_dir = settings.NOTES_DIR / str(course_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        version = 1
        parent_id = None

        if replace_note_id:
            result = await self.db.execute(select(Note).where(Note.id == replace_note_id))
            old_note = result.scalar_one_or_none()
            if old_note:
                await self.db.execute(
                    update(Note).where(Note.id == replace_note_id).values(is_current=False)
                )
                version = old_note.version + 1
                parent_id = replace_note_id

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = f"v{version}_{ts}_{file_name}"
        dest_path = dest_dir / safe_name
        dest_path.write_bytes(file_bytes)

        note = Note(
            course_id=course_id,
            title=title,
            unit=unit,
            topic=topic,
            file_path=str(dest_path),
            file_name=file_name,
            version=version,
            is_current=True,
            parent_id=parent_id,
            uploaded_by=uploaded_by,
            lesson_id=lesson_id,
            chapter_id=chapter_id,
            created_at=datetime.utcnow(),
        )
        validation = validate_notes_upload(note)
        if not validation.passed:
            raise ValueError(f"Note validation failed: {validation.diagnosis}")

        self.db.add(note)
        await self.db.flush()

        await self.audit.log(
            self.AGENT_NAME, "note_uploaded",
            entity_type="Note", entity_id=note.id,
            input_data={"title": title, "unit": unit, "topic": topic, "version": version},
            output_data={"note_id": note.id, "path": str(dest_path)},
        )
        return note

    async def list_versions(self, note_id: int):
        result = await self.db.execute(
            select(Note).where(Note.parent_id == note_id).order_by(Note.version)
        )
        return result.scalars().all()

    async def restore_version(self, note_id: int, faculty_id: int) -> Note:
        result = await self.db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        if not note:
            raise ValueError("Note not found")
        await self.db.execute(
            update(Note).where(Note.course_id == note.course_id).values(is_current=False)
        )
        await self.db.execute(update(Note).where(Note.id == note_id).values(is_current=True))
        await self.audit.log(
            self.AGENT_NAME, "note_version_restored",
            entity_type="Note", entity_id=note_id,
            input_data={"restored_by": faculty_id},
            output_data={"note_id": note_id, "is_current": True},
        )
        return note

    async def delete_note(self, note_id: int, faculty_id: int) -> bool:
        result = await self.db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        if not note:
            raise ValueError("Note not found")
        
        file_p = Path(note.file_path)
        if file_p.exists():
            try:
                file_p.unlink()
            except Exception:
                pass
        
        await self.db.delete(note)
        await self.audit.log(
            self.AGENT_NAME, "note_deleted",
            entity_type="Note", entity_id=note_id,
            input_data={"deleted_by": faculty_id, "file_name": note.file_name},
            output_data={"note_id": note_id, "deleted": True},
        )
        return True
