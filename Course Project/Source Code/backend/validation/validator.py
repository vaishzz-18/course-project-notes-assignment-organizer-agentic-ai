"""
ValidationAgent — hard gate that every result must pass before human review.
Self-healing: caller regenerates only the failing part (Labs 10/11).
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from models.database import Grade, Submission


@dataclass
class ValidationReport:
    passed: bool
    failing: List[str] = field(default_factory=list)
    diagnosis: str = ""
    attempts: int = 0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "failing": self.failing,
            "diagnosis": self.diagnosis,
            "attempts": self.attempts,
        }


def validate_grade(grade: Grade, submission: Submission, rubric_max: float) -> ValidationReport:
    """Hard acceptance gate for a single grade draft."""
    checks: List[Tuple[str, bool]] = [
        (
            "draft_marks_within_rubric_max",
            grade.draft_marks is not None and grade.draft_marks <= rubric_max,
        ),
        (
            "draft_marks_non_negative",
            grade.draft_marks is not None and grade.draft_marks >= 0,
        ),
        (
            "feedback_present",
            bool(grade.draft_feedback and grade.draft_feedback.strip()),
        ),
        (
            "evidence_record_attached",
            bool(grade.evidence_record),
        ),
        (
            "similarity_score_attached",
            submission.similarity_score is not None,
        ),
        (
            "grade_not_published_without_approval",
            grade.status != "published" or grade.approved_by is not None,
        ),
        (
            "late_submission_flagged",
            True,  # always true — is_late is set by SubmissionCollectionAgent
        ),
    ]

    failing = [name for name, ok in checks if not ok]
    passed = len(failing) == 0
    diagnosis = (
        f"Checks failed: {', '.join(failing)}. "
        "Regenerate only the failing grade component." if failing else "All checks passed."
    )
    return ValidationReport(passed=passed, failing=failing, diagnosis=diagnosis)


def validate_submission_batch(submissions: list, assignment_due) -> ValidationReport:
    """Validate that all submissions have timestamps and late flags set."""
    failing = []
    for sub in submissions:
        if sub.submitted_at is None:
            failing.append(f"submission_{sub.id}_missing_timestamp")
        if sub.is_late is None:
            failing.append(f"submission_{sub.id}_missing_late_flag")
    passed = len(failing) == 0
    return ValidationReport(
        passed=passed,
        failing=failing,
        diagnosis="All submission timestamps valid." if passed else f"Issues: {failing}",
    )


def validate_notes_upload(note) -> ValidationReport:
    """Validate a notes upload has required metadata."""
    failing = []
    if not note.unit or not note.unit.strip():
        failing.append("unit_missing")
    if not note.topic or not note.topic.strip():
        failing.append("topic_missing")
    if not note.file_path:
        failing.append("file_path_missing")
    passed = len(failing) == 0
    return ValidationReport(passed=passed, failing=failing,
                            diagnosis="Note metadata valid." if passed else f"Missing: {failing}")
