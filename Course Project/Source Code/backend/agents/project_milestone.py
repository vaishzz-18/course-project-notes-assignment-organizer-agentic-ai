"""Project Milestone Tracking Agent — tracks each group's progress against defined checkpoints."""
import json
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import (
    Milestone, MilestoneProgress, MilestoneProgressStatus, MilestoneHealth, ProjectGroup, ProjectFeedback, User
)
from runtime.audit import AuditLogger


def _compute_health(milestone: Milestone, progress: MilestoneProgress) -> str:
    now = datetime.utcnow()
    if progress.status == MilestoneProgressStatus.approved:
        return MilestoneHealth.green
    if progress.status == MilestoneProgressStatus.submitted:
        return MilestoneHealth.green
    days_left = (milestone.due_date - now).days
    if days_left < 0:
        return MilestoneHealth.red
    if days_left < 3:
        return MilestoneHealth.amber
    return MilestoneHealth.green


class ProjectMilestoneAgent:
    AGENT_NAME = "ProjectMilestoneAgent"

    def __init__(self, db: AsyncSession, audit: AuditLogger):
        self.db = db
        self.audit = audit

    async def step(self, milestone_ids: List[int]) -> List[dict]:
        """Pipeline step: check progress for each milestone and update health."""
        results = []
        for mid in milestone_ids:
            result = await self.db.execute(select(Milestone).where(Milestone.id == mid))
            milestone = result.scalar_one_or_none()
            if not milestone:
                continue

            prog_result = await self.db.execute(
                select(MilestoneProgress).where(MilestoneProgress.milestone_id == mid)
            )
            progresses = prog_result.scalars().all()

            for prog in progresses:
                health = _compute_health(milestone, prog)
                prog.health = health
                await self.db.flush()
                results.append({
                    "milestone_id": mid,
                    "group_id": prog.group_id,
                    "health": health,
                    "status": prog.status,
                })

        await self.audit.log(
            self.AGENT_NAME, "milestone_check_complete",
            input_data={"milestone_ids": milestone_ids},
            output_data={"checked": len(results)},
        )
        return results

    async def submit_progress(
        self,
        milestone_id: int,
        group_id: int,
        notes: str,
        file_bytes: bytes = None,
        file_name: str = None,
        github_url: str = None,
    ) -> MilestoneProgress:
        result = await self.db.execute(
            select(MilestoneProgress).where(
                MilestoneProgress.milestone_id == milestone_id,
                MilestoneProgress.group_id == group_id,
            )
        )
        prog = result.scalar_one_or_none()

        file_path = None
        if file_bytes and file_name:
            from config import settings
            dest_dir = settings.UPLOAD_DIR / "milestones" / str(milestone_id)
            dest_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            dest_path = dest_dir / f"group_{group_id}_{ts}_{file_name}"
            dest_path.write_bytes(file_bytes)
            file_path = str(dest_path)

        if prog:
            prog.status = MilestoneProgressStatus.submitted
            prog.notes = notes
            if github_url:
                prog.github_url = github_url
            prog.submitted_at = datetime.utcnow()
            if file_path:
                prog.submission_file = file_path
        else:
            milestone = await self.db.get(Milestone, milestone_id)
            prog = MilestoneProgress(
                milestone_id=milestone_id,
                group_id=group_id,
                status=MilestoneProgressStatus.submitted,
                notes=notes,
                submission_file=file_path,
                github_url=github_url,
                submitted_at=datetime.utcnow(),
                health=MilestoneHealth.green,
            )
            self.db.add(prog)

        if github_url:
            group = await self.db.get(ProjectGroup, group_id)
            if group:
                group.github_url = github_url

        await self.db.flush()
        await self.audit.log(
            self.AGENT_NAME, "milestone_progress_submitted",
            entity_type="MilestoneProgress", entity_id=prog.id if prog.id else 0,
            input_data={"milestone_id": milestone_id, "group_id": group_id},
            output_data={"status": prog.status},
        )
        return prog

    async def get_course_summary(self, course_id: int) -> List[dict]:
        milestones_result = await self.db.execute(
            select(Milestone).where(Milestone.course_id == course_id).order_by(Milestone.checkpoint_number)
        )
        milestones = milestones_result.scalars().all()

        # Load all feedback records for this course mapped by (group_id, milestone_id, category)
        fb_result = await self.db.execute(
            select(ProjectFeedback, User.name)
            .join(User, User.id == ProjectFeedback.faculty_id)
            .where(ProjectFeedback.course_id == course_id)
        )
        fb_rows = fb_result.all()
        feedback_map = {}
        for fb, fac_name in fb_rows:
            key = (fb.group_id, fb.milestone_id, fb.category)
            feedback_map[key] = {
                "id": fb.id,
                "feedback_text": fb.feedback_text,
                "category": fb.category,
                "faculty_id": fb.faculty_id,
                "faculty_name": fac_name,
                "created_at": fb.created_at.isoformat() if fb.created_at else None,
                "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
            }

        summary = []
        for ms in milestones:
            prog_result = await self.db.execute(
                select(MilestoneProgress).where(MilestoneProgress.milestone_id == ms.id)
            )
            progresses = prog_result.scalars().all()
            if not progresses:
                summary.append({
                    "milestone_id": ms.id,
                    "milestone_title": ms.title,
                    "checkpoint_number": ms.checkpoint_number,
                    "due_date": ms.due_date.isoformat(),
                    "group_id": None,
                    "group_name": "No Groups Formed",
                    "status": "not_started",
                    "health": "green",
                    "notes": None,
                    "github_url": None,
                    "submission_file": None,
                    "submitted_at": None,
                    "checkpoint_feedback": None,
                    "github_feedback": None,
                })
            else:
                for prog in progresses:
                    group = await self.db.get(ProjectGroup, prog.group_id)
                    cp_fb = feedback_map.get((prog.group_id, ms.id, "checkpoint"))
                    gh_fb = feedback_map.get((prog.group_id, ms.id, "github")) or feedback_map.get((prog.group_id, None, "github"))
                    summary.append({
                        "milestone_id": ms.id,
                        "milestone_title": ms.title,
                        "checkpoint_number": ms.checkpoint_number,
                        "due_date": ms.due_date.isoformat(),
                        "group_id": prog.group_id,
                        "group_name": group.name if group else "Unknown",
                        "status": prog.status,
                        "health": prog.health,
                        "notes": prog.notes,
                        "github_url": prog.github_url or (group.github_url if group else None),
                        "submission_file": prog.submission_file,
                        "submitted_at": prog.submitted_at.isoformat() if prog.submitted_at else None,
                        "checkpoint_feedback": cp_fb,
                        "github_feedback": gh_fb,
                    })
        return summary
