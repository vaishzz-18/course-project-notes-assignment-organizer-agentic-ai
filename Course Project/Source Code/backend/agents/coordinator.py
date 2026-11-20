"""
apniLeap AURA Coordinator — owns run-state, plan, budgets and audit log.
Orchestrates the full pipeline; enforces the human gate before publish.
"""
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.audit import AuditLogger, new_run_id
from runtime.governance import GovernanceEngine
from connector.data_connector import DataConnector
from skills.plan_skill import build_grade_plan, Plan
from config import settings


class AURACoordinator:
    AGENT_NAME = "AURACoordinator"

    def __init__(self, db: AsyncSession, actor_id: Optional[int] = None):
        self.db = db
        self.run_id = new_run_id()
        self.audit = AuditLogger(db, self.run_id, actor_id)
        self.governance = GovernanceEngine(db, self.audit)
        self.connector = DataConnector(db)
        self.state: dict = {}
        self.attempts = 0

    async def initialize(self, plan: Plan) -> str:
        await self.governance.create_run(self.run_id, plan.to_dict())
        await self.audit.log(
            self.AGENT_NAME, "run_initialized",
            input_data={"task_type": plan.task_type, "units": len(plan.units)},
        )
        return self.run_id

    async def checkpoint(self):
        await self.governance.checkpoint(self.run_id, self.state)

    async def complete(self):
        await self.governance.complete_run(self.run_id)
        await self.audit.log(self.AGENT_NAME, "run_completed", output_data=self.state)

    async def escalate(self, reason: str):
        await self.governance.fail_run(self.run_id, reason)
        await self.audit.log(
            self.AGENT_NAME, "escalated_to_faculty",
            output_data={"reason": reason}, status="escalated"
        )

    async def run_grading_pipeline(self, course_id: int, assignment_id: int) -> dict:
        """Full grading pipeline: collect → similarity → grade → validate → queue for faculty."""
        from datetime import datetime
        from agents.submission_collection import SubmissionCollectionAgent
        from agents.plagiarism_similarity import PlagiarismSimilarityAgent
        from agents.grading_assistance import GradingAssistanceAgent
        from validation.validator import validate_grade
        from models.database import Assignment, CourseEnrollment, Submission

        from sqlalchemy import select
        result = await self.db.execute(select(Assignment).where(Assignment.id == assignment_id))
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")

        rubric = json.loads(assignment.rubric) if assignment.rubric else {}
        rubric_max = assignment.max_marks

        # 1. Identify enrolled students who have not submitted
        enrollment_result = await self.db.execute(
            select(CourseEnrollment.student_id).where(CourseEnrollment.course_id == course_id)
        )
        enrolled_student_ids = set(enrollment_result.scalars().all())

        existing_subs = await self.connector.read_submissions(assignment_id=assignment_id)
        submitted_student_ids = {s.student_id for s in existing_subs}
        missing_student_ids = enrolled_student_ids - submitted_student_ids

        # Create missing submission records for non-submitting students
        for sid in missing_student_ids:
            missing_sub = Submission(
                assignment_id=assignment_id,
                student_id=sid,
                file_path="",
                file_name="No Submission",
                submitted_at=datetime.utcnow(),
                is_late=True,
                status="not_submitted",
                similarity_score=0.0,
                similarity_flags=json.dumps([]),
            )
            self.db.add(missing_sub)

        if missing_student_ids:
            await self.db.flush()

        submissions = await self.connector.read_submissions(assignment_id=assignment_id)
        plan = build_grade_plan(self.run_id, course_id, [s.id for s in submissions], rubric_max)
        await self.initialize(plan)

        sub_agent = SubmissionCollectionAgent(self.db, self.audit)
        sim_agent = PlagiarismSimilarityAgent(self.db, self.audit)
        grade_agent = GradingAssistanceAgent(self.db, self.audit)

        results = []
        for sub in submissions:
            await sub_agent.step(sub, assignment.due_date)
            await self.checkpoint()

        # Run similarity only on active submissions with files
        active_subs = [s for s in submissions if s.file_path and s.status != "not_submitted"]
        if active_subs:
            await sim_agent.step(active_subs)
            await self.checkpoint()

        for sub in submissions:
            if sub.status == "not_submitted" and sub.similarity_score is None:
                sub.similarity_score = 0.0

            grade = await grade_agent.step(sub, assignment, rubric)
            report = validate_grade(grade, sub, rubric_max)

            regen_attempts = 0
            while not report.passed and regen_attempts < settings.MAX_VALIDATION_ATTEMPTS:
                regen_attempts += 1
                await self.audit.log(
                    self.AGENT_NAME, "validation_failed_regenerate",
                    input_data={"submission_id": sub.id, "failing": report.failing, "attempt": regen_attempts}
                )
                grade = await grade_agent.step(sub, assignment, rubric)
                report = validate_grade(grade, sub, rubric_max)

            if not report.passed:
                await self.escalate(f"Validation failed for submission {sub.id}: {report.diagnosis}")
                results.append({"submission_id": sub.id, "status": "escalated", "report": report.to_dict()})
            else:
                results.append({"submission_id": sub.id, "grade_id": grade.id, "status": "pending_approval"})

        self.state["results"] = results
        await self.complete()
        await self.db.commit()
        return {"run_id": self.run_id, "results": results}

    async def grade_single_submission(self, submission_id: int) -> dict:
        """Grade a single submission on demand: cross-check similarity with peers -> AI rubric grade -> validate -> queue."""
        from agents.plagiarism_similarity import PlagiarismSimilarityAgent
        from agents.grading_assistance import GradingAssistanceAgent
        from validation.validator import validate_grade
        from models.database import Assignment, Submission, User
        from sqlalchemy import select

        sub_res = await self.db.execute(select(Submission).where(Submission.id == submission_id))
        sub = sub_res.scalar_one_or_none()
        if not sub:
            raise ValueError(f"Submission {submission_id} not found")

        asgn_res = await self.db.execute(select(Assignment).where(Assignment.id == sub.assignment_id))
        assignment = asgn_res.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {sub.assignment_id} not found")

        rubric = json.loads(assignment.rubric) if assignment.rubric else {}
        rubric_max = assignment.max_marks

        # Run similarity across all active submissions for this assignment so cross-check is complete
        all_subs = await self.connector.read_submissions(assignment_id=assignment.id)
        active_subs = [s for s in all_subs if s.file_path and s.status != "not_submitted"]
        if active_subs:
            sim_agent = PlagiarismSimilarityAgent(self.db, self.audit)
            await sim_agent.step(active_subs)

        if sub.status == "not_submitted" and sub.similarity_score is None:
            sub.similarity_score = 0.0

        grade_agent = GradingAssistanceAgent(self.db, self.audit)
        grade = await grade_agent.step(sub, assignment, rubric)
        report = validate_grade(grade, sub, rubric_max)

        regen_attempts = 0
        while not report.passed and regen_attempts < settings.MAX_VALIDATION_ATTEMPTS:
            regen_attempts += 1
            await self.audit.log(
                self.AGENT_NAME, "validation_failed_regenerate",
                input_data={"submission_id": sub.id, "failing": report.failing, "attempt": regen_attempts}
            )
            grade = await grade_agent.step(sub, assignment, rubric)
            report = validate_grade(grade, sub, rubric_max)

        await self.db.commit()

        # Fetch student info for clean response
        u_res = await self.db.execute(select(User).where(User.id == sub.student_id))
        student = u_res.scalar_one_or_none()

        return {
            "success": True,
            "submission_id": sub.id,
            "student_id": sub.student_id,
            "student_name": student.name if student else "Unknown",
            "assignment_id": assignment.id,
            "assignment_title": assignment.title,
            "draft_marks": grade.draft_marks,
            "max_marks": assignment.max_marks,
            "status": grade.status.value if hasattr(grade.status, "value") else str(grade.status),
            "draft_feedback": grade.draft_feedback,
            "draft_rubric_breakdown": json.loads(grade.draft_rubric_breakdown) if grade.draft_rubric_breakdown else {},
            "similarity_score": sub.similarity_score,
            "similarity_flags": json.loads(sub.similarity_flags) if sub.similarity_flags else [],
            "evidence_record": json.loads(grade.evidence_record) if grade.evidence_record else {},
            "validation_passed": report.passed,
        }
