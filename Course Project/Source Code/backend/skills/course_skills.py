"""
Lab 3: Skill Creation — Reusable Plan & Format Skills
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Package repeatable capabilities as reusable, schema-typed skills.

Acceptance Criteria:
Two callable skills with schemas, invoked by the agent.
The same skill works for two different cases (e.g., Theory Course vs Lab Course)
without code changes.

Pseudocode:
skill plan(inputs) -> Plan: return expand(inputs).lock()
skill format_organised(result, template) -> Document
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import json


# ---------------------------------------------------------------------------
# Skill 1: PlanSkill (Schema-Typed & Immutable)
# ---------------------------------------------------------------------------

class CriterionSchema(BaseModel):
    name: str
    weight: float
    description: str = ""


class AssignmentSpecSchema(BaseModel):
    assignment_id: str
    title: str
    unit_reference: str
    max_marks: float
    rubric: List[CriterionSchema]
    is_coding_task: bool = False


class MilestoneSpecSchema(BaseModel):
    checkpoint_number: int
    title: str
    deliverable: str
    week_deadline: int


class PlanInputSchema(BaseModel):
    course_name: str
    course_code: str
    course_type: Literal["theory", "lab", "hybrid"] = "hybrid"
    faculty_lead: str
    units: List[str]
    assignments: List[AssignmentSpecSchema]
    milestones: List[MilestoneSpecSchema]
    similarity_threshold: float = 0.75
    allow_late_submissions: bool = True
    late_penalty_percent_per_day: float = 5.0


class PlanUnitSlot(BaseModel):
    slot_id: str
    entity_type: Literal["unit_notes", "assignment_brief", "submission_eval", "milestone_checkpoint"]
    entity_ref: str
    constraints: Dict[str, Any] = Field(default_factory=dict)


class LockedPlanSchema(BaseModel):
    plan_id: str
    plan_fingerprint: str  # SHA-256 hash guaranteeing tamper-proof immutability
    course_name: str
    course_code: str
    course_type: str
    faculty_lead: str
    slots: List[PlanUnitSlot]
    assignments: List[AssignmentSpecSchema]
    milestones: List[MilestoneSpecSchema]
    similarity_threshold: float
    is_locked: bool = True
    locked_at: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class PlanSkill:
    """
    Skill 1: Plan / Blueprint Skill
    Expands high-level course specifications into an immutable, hashed execution plan.
    Case-agnostic: Works identically for Theory courses, Lab courses, or Hybrid courses.
    """

    SKILL_NAME = "PlanSkill"
    VERSION = "2.0.0"

    def execute(self, inputs: PlanInputSchema) -> LockedPlanSchema:
        now_str = datetime.utcnow().isoformat()
        plan_id = f"plan_{inputs.course_code.lower()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        slots: List[PlanUnitSlot] = []

        # 1. Notes slots per unit
        for u in inputs.units:
            slots.append(PlanUnitSlot(
                slot_id=f"slot_notes_{u.lower().replace(' ', '_')}",
                entity_type="unit_notes",
                entity_ref=u,
                constraints={"versioned": True, "immutable_archive": True}
            ))

        # 2. Assignment distribution & grading slots
        for a in inputs.assignments:
            slots.append(PlanUnitSlot(
                slot_id=f"slot_assign_{a.assignment_id}",
                entity_type="assignment_brief",
                entity_ref=a.title,
                constraints={
                    "max_marks": a.max_marks,
                    "rubric_count": len(a.rubric),
                    "is_coding": a.is_coding_task,
                    "similarity_check_required": True
                }
            ))

        # 3. Milestone checkpoints
        for m in inputs.milestones:
            slots.append(PlanUnitSlot(
                slot_id=f"slot_ms_{m.checkpoint_number}",
                entity_type="milestone_checkpoint",
                entity_ref=m.title,
                constraints={"week": m.week_deadline, "health_tracking": True}
            ))

        # Calculate cryptographic fingerprint
        raw_repr = f"{inputs.course_code}|{inputs.course_name}|{len(slots)}|{inputs.similarity_threshold}|{now_str}"
        fingerprint = hashlib.sha256(raw_repr.encode()).hexdigest()[:16]

        return LockedPlanSchema(
            plan_id=plan_id,
            plan_fingerprint=f"sha256:{fingerprint}",
            course_name=inputs.course_name,
            course_code=inputs.course_code,
            course_type=inputs.course_type,
            faculty_lead=inputs.faculty_lead,
            slots=slots,
            assignments=inputs.assignments,
            milestones=inputs.milestones,
            similarity_threshold=inputs.similarity_threshold,
            is_locked=True,
            locked_at=now_str,
            meta={
                "slots_count": len(slots),
                "penalty_rule": f"{inputs.late_penalty_percent_per_day}% per day late",
                "human_gate_required": True
            }
        )


# ---------------------------------------------------------------------------
# Skill 2: FormatSkill (Multi-Template Workspace Renderer)
# ---------------------------------------------------------------------------

class FormatInputSchema(BaseModel):
    plan: LockedPlanSchema
    notes_summary: List[Dict[str, Any]]
    submissions_summary: List[Dict[str, Any]]
    milestones_summary: List[Dict[str, Any]]
    template_type: Literal["markdown", "html", "compact_text"] = "markdown"


class FormattedDocumentSchema(BaseModel):
    document_id: str
    course_code: str
    template_type: str
    content: str
    rendered_at: str
    signoff_required: bool = True


class FormatSkill:
    """
    Skill 2: Format Skill
    Renders structured course workspace state into human-readable publications.
    Case-agnostic: Renders theory syllabi and lab code ledgers uniformly.
    """

    SKILL_NAME = "FormatSkill"
    VERSION = "2.0.0"

    def execute(self, inputs: FormatInputSchema) -> FormattedDocumentSchema:
        doc_id = f"doc_workspace_{inputs.plan.course_code.lower()}_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        now_formatted = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        if inputs.template_type == "markdown":
            content = self._render_markdown(inputs, now_formatted)
        elif inputs.template_type == "html":
            content = self._render_html(inputs, now_formatted)
        else:
            content = self._render_compact(inputs, now_formatted)

        return FormattedDocumentSchema(
            document_id=doc_id,
            course_code=inputs.plan.course_code,
            template_type=inputs.template_type,
            content=content,
            rendered_at=now_formatted,
            signoff_required=True
        )

    def _render_markdown(self, inputs: FormatInputSchema, timestamp: str) -> str:
        p = inputs.plan
        lines = [
            f"# COURSE WORKSPACE: {p.course_code} — {p.course_name.upper()}",
            f"**Course Type**: {p.course_type.capitalize()} | **Faculty Lead**: {p.faculty_lead}",
            f"**Plan Fingerprint**: `{p.plan_fingerprint}` | **Generated**: {timestamp}",
            "=" * 70,
            "",
            "## 1. VERSIONED NOTES & MATERIALS REPOSITORY",
            "| Unit / Module | Topic | Version | Status | Resource Path |",
            "|---|---|---|---|---|"
        ]

        for n in inputs.notes_summary:
            status_badge = "Current" if n.get("is_current", True) else "Archived"
            lines.append(f"| {n.get('unit', 'Unit')} | {n.get('topic', 'Topic')} | v{n.get('version', 1)} | {status_badge} | `{n.get('file_name', 'n/a')}` |")

        lines += [
            "",
            "## 2. ASSIGNMENT & GRADING QUEUE",
            "| Assignment | Max Marks | Coding Task | Status | Similarity Flag |",
            "|---|---|---|---|---|"
        ]

        for a in p.assignments:
            coding_flag = "Yes (Automated Test)" if a.is_coding_task else "No (Text/Proof)"
            lines.append(f"| {a.title} | {a.max_marks} marks | {coding_flag} | Active | <= {p.similarity_threshold:.0%} |")

        lines += [
            "",
            "### Student Submission Ledger:",
            "| Student | Status | Timing | Similarity | Draft Score |",
            "|---|---|---|---|---|"
        ]

        for s in inputs.submissions_summary:
            flag = f"⚠ **HIGH ({s.get('similarity', 0):.0%})**" if s.get("similarity", 0) > p.similarity_threshold else f"{s.get('similarity', 0):.0%}"
            lines.append(f"| {s.get('student_name')} | {s.get('status')} | {s.get('timing')} | {flag} | {s.get('draft_score', 'Pending')} |")

        lines += [
            "",
            "## 3. PROJECT MILESTONE TRACKER",
            "| Checkpoint # | Milestone Deliverable | Target Week | Health |",
            "|---|---|---|---|"
        ]

        for m in inputs.milestones_summary:
            lines.append(f"| Checkpoint {m.get('checkpoint')} | {m.get('title')} | Week {m.get('week')} | **{m.get('health', 'GREEN').upper()}** |")

        lines += [
            "",
            "=" * 70,
            "### FACULTY APPROVAL & GOVERNANCE GATE",
            "> [!IMPORTANT]",
            f"> Draft only. In accordance with Chapter 2 governance, grades and feedback require course faculty ({p.faculty_lead}) sign-off before publishing.",
            "",
            "**Course Faculty Decision**: [ ] APPROVE   [ ] EDIT   [ ] OVERRIDE",
            f"**Signed**: ___________________________ Date: _____________"
        ]

        return "\n".join(lines)

    def _render_html(self, inputs: FormatInputSchema, timestamp: str) -> str:
        p = inputs.plan
        return f"""<div class="course-workspace">
  <h2>{p.course_code}: {p.course_name}</h2>
  <p><strong>Faculty:</strong> {p.faculty_lead} | <strong>Fingerprint:</strong> {p.plan_fingerprint}</p>
  <div class="audit-badge">Draft for Review — Human Gate Enforced</div>
</div>"""

    def _render_compact(self, inputs: FormatInputSchema, timestamp: str) -> str:
        p = inputs.plan
        return f"[{p.course_code}] {p.course_name} | Plan {p.plan_id} | {len(p.slots)} Slots | Faculty: {p.faculty_lead}"
