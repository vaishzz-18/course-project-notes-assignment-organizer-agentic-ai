"""Lab 3 — Plan skill: schema-typed, reusable, case-agnostic."""
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class PlanUnit:
    unit_id: str
    entity_type: str       # "submission" | "note" | "milestone_check"
    entity_id: int
    constraints: dict = field(default_factory=dict)


@dataclass
class Plan:
    run_id: str
    course_id: int
    task_type: str         # "grade_batch" | "distribute" | "check_milestones"
    units: List[PlanUnit] = field(default_factory=list)
    locked: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    meta: dict = field(default_factory=dict)

    def lock(self) -> "Plan":
        self.locked = True
        return self

    def to_dict(self) -> dict:
        return asdict(self)


def build_grade_plan(run_id: str, course_id: int, submission_ids: List[int], rubric_max: float) -> Plan:
    units = [
        PlanUnit(
            unit_id=f"sub_{sid}",
            entity_type="submission",
            entity_id=sid,
            constraints={"max_marks": rubric_max},
        )
        for sid in submission_ids
    ]
    return Plan(run_id=run_id, course_id=course_id, task_type="grade_batch", units=units).lock()


def build_distribution_plan(run_id: str, course_id: int, assignment_id: int, student_ids: List[int]) -> Plan:
    units = [
        PlanUnit(unit_id=f"student_{sid}", entity_type="student", entity_id=sid, constraints={})
        for sid in student_ids
    ]
    return Plan(
        run_id=run_id, course_id=course_id, task_type="distribute",
        units=units, meta={"assignment_id": assignment_id}
    ).lock()


def build_milestone_plan(run_id: str, course_id: int, milestone_ids: List[int]) -> Plan:
    units = [
        PlanUnit(unit_id=f"ms_{mid}", entity_type="milestone_check", entity_id=mid, constraints={})
        for mid in milestone_ids
    ]
    return Plan(run_id=run_id, course_id=course_id, task_type="check_milestones", units=units).lock()
