"""
Lab 12: Safety & Governance — Approval, Eval, Rollback
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Add access control, confidentiality, the course faculty approval gate as a hard stop,
evaluation metrics, versioning, and one-click rollback.

Guiding Design Principle:
  • Agents draft and flag; a named human approves.
  • Never publish a grade or feedback without faculty approval.
  • Strict confidentiality: students cannot view peers' submissions or unapproved drafts.
  • One-click rollback restores any prior version cleanly.

Pseudocode (from Chapter 2):
  require actor.can_approve and out.status == 'draft'
  final = apply(human.edits, out); final.status = 'approved'
  governance.publish(final, version=v+1); metrics.record(...)
  on rollback(v): restore(version=v)
"""

from __future__ import annotations

import copy
import statistics
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from runtime.governed_runtime import AURAControlledRuntime


# ── Data Models ───────────────────────────────────────────────────────────────

class RoleContext(BaseModel):
    """Execution identity and role permissions for access control."""
    user_id: int
    name: str
    role: Literal["faculty", "student", "hod", "anonymous"] = "student"
    can_approve: bool = False
    can_view_all_submissions: bool = False

    @classmethod
    def faculty(cls, user_id: int = 1, name: str = "Dr. Vaishnavi Patel") -> RoleContext:
        return cls(user_id=user_id, name=name, role="faculty", can_approve=True, can_view_all_submissions=True)

    @classmethod
    def student(cls, user_id: int = 5, name: str = "Alex Chen") -> RoleContext:
        return cls(user_id=user_id, name=name, role="student", can_approve=False, can_view_all_submissions=False)

    @classmethod
    def hod(cls, user_id: int = 99, name: str = "Head of Department") -> RoleContext:
        return cls(user_id=user_id, name=name, role="hod", can_approve=True, can_view_all_submissions=True)


class EvaluationMetrics(BaseModel):
    """Statistical and operational evaluation metrics recorded on release."""
    release_id: str
    total_submissions: int
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    grade_distribution: Dict[str, int]
    plagiarism_quarantine_count: int
    late_penalty_count: int
    human_edits_count: int
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HumanEditRecord(BaseModel):
    """Record of a named human faculty member modifying an agent draft."""
    submission_id: str
    student_name: str
    original_score: float
    adjusted_score: float
    faculty_reason: str
    edited_by: str
    edited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VersionedRelease(BaseModel):
    """Governed, versioned, and auditable course workspace release."""
    release_id: str
    version: int
    course_id: int
    course_code: str
    status: Literal["draft", "approved", "published", "rolled_back"]
    approved_by: str
    approved_by_id: int
    workspace_snapshot: Dict[str, Any]
    metrics: EvaluationMetrics
    human_edits: List[HumanEditRecord] = Field(default_factory=list)
    published_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RollbackResult(BaseModel):
    """Outcome of a 1-click rollback restoration."""
    course_id: int
    target_version: int
    restored_release_id: str
    active_version: int
    rolled_back_by: str
    restored_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    restored_workspace: Dict[str, Any]


# ── Safety & Governance Manager ───────────────────────────────────────────────

class SafetyGovernanceManager:
    """
    Lab 12: Safety & Governance Manager.
    
    Implements:
      1. Role-based Confidentiality Filters
      2. Formal Course Faculty Approval Gate
      3. Versioned Release Publishing (v1, v2...)
      4. Evaluation Metrics Logging
      5. One-Click Instant Rollback with Audit Trails
    """

    def __init__(self, runtime: Optional[AURAControlledRuntime] = None):
        self.runtime = runtime or AURAControlledRuntime()
        # In-memory version history indexed by course_id -> {version_number: VersionedRelease}
        self.version_history: Dict[int, Dict[int, VersionedRelease]] = {}
        self.active_versions: Dict[int, int] = {}

    # ── 1. Confidentiality & Access Control ───────────────────────────────────

    def enforce_confidentiality(
        self,
        workspace: Dict[str, Any],
        actor: RoleContext
    ) -> Dict[str, Any]:
        """
        Enforces strict confidentiality:
          • Faculty / HoD: full visibility into all submissions, similarity flags, and audit logs.
          • Student: can ONLY see their own submission and their own approved grade.
                     Cannot see peers' work, peer similarity scores, or unapproved draft grades.
        """
        sanitized = copy.deepcopy(workspace)

        if actor.can_view_all_submissions:
            sanitized["access_level"] = "UNRESTRICTED_FACULTY_VIEW"
            return sanitized

        # Student restricted view
        sanitized["access_level"] = f"RESTRICTED_STUDENT_VIEW (User #{actor.user_id}: {actor.name})"

        # 1. Filter submissions to only the actor's own work
        own_submissions = [
            s for s in sanitized.get("submissions", [])
            if s.get("student_name") == actor.name or s.get("student_id") == actor.user_id
        ]
        sanitized["submissions"] = own_submissions

        # 2. Filter grades & mask unapproved drafts
        is_published = sanitized.get("status") == "published" and sanitized.get("faculty_approved", False)
        own_grades = []
        for g in sanitized.get("grading_results", []):
            if g.get("student_name") == actor.name:
                g_copy = copy.deepcopy(g)
                if not is_published:
                    g_copy["final_score"] = "PENDING_FACULTY_APPROVAL"
                    g_copy["raw_score"] = "PENDING_FACULTY_APPROVAL"
                    g_copy["feedback"] = "Grade draft is currently pending faculty review."
                own_grades.append(g_copy)

        sanitized["grading_results"] = own_grades

        # 3. Strip internal agent audit traces and similarity flags of peers
        sanitized.pop("evidence_table", None)
        sanitized.pop("audit_trail", None)
        sanitized.pop("similarity_flags", None)

        return sanitized

    # ── 2. Approval Workflow & Version Publishing ─────────────────────────────

    def review_and_approve(
        self,
        draft: Dict[str, Any],
        actor: RoleContext,
        human_edits: Optional[List[Dict[str, Any]]] = None
    ) -> VersionedRelease:
        """
        Executes Chapter 2 pseudocode:
          require actor.can_approve and out.status == 'draft'
          final = apply(human.edits, out); final.status = 'approved'
          governance.publish(final, version=v+1); metrics.record(...)
        """
        # Invariant 1: Actor authorization
        if not actor.can_approve:
            raise PermissionError(
                f"Unauthorized action: Actor '{actor.name}' with role '{actor.role}' cannot approve grades. "
                "Only named Course Faculty can approve."
            )

        # Invariant 2: Draft status check
        current_status = draft.get("status", "draft")
        if current_status not in ("draft", "draft_pending_faculty_review"):
            raise ValueError(f"Cannot approve workspace with status '{current_status}'. Status must be 'draft'.")

        course_id = draft.get("course_id", 1)
        course_code = draft.get("course_code", "CS401")

        final_workspace = copy.deepcopy(draft)
        applied_edits: List[HumanEditRecord] = []

        # Apply human faculty edits if provided
        if human_edits:
            for edit in human_edits:
                sub_id = str(edit.get("submission_id"))
                new_score = float(edit.get("new_score", 0.0))
                reason = edit.get("reason", "Faculty manual grade adjustment")

                for g in final_workspace.get("grading_results", []):
                    if str(g.get("submission_id")) == sub_id:
                        old_score = float(g.get("final_score", 0.0))
                        g["final_score"] = new_score
                        g["faculty_override"] = True
                        g["faculty_override_reason"] = reason

                        applied_edits.append(
                            HumanEditRecord(
                                submission_id=sub_id,
                                student_name=g.get("student_name", "Unknown"),
                                original_score=old_score,
                                adjusted_score=new_score,
                                faculty_reason=reason,
                                edited_by=actor.name,
                            )
                        )

        # Update status
        final_workspace["status"] = "published"
        final_workspace["faculty_approved"] = True
        final_workspace["approved_by"] = actor.name
        final_workspace["approved_at"] = datetime.now(timezone.utc).isoformat()

        # Compute next version number
        if course_id not in self.version_history:
            self.version_history[course_id] = {}
        current_v = self.active_versions.get(course_id, 0)
        next_v = current_v + 1
        release_id = f"rel_{course_code.lower()}_v{next_v}_{uuid.uuid4().hex[:6]}"

        # Record evaluation metrics
        metrics = self._calculate_evaluation_metrics(final_workspace, release_id, len(applied_edits))

        release = VersionedRelease(
            release_id=release_id,
            version=next_v,
            course_id=course_id,
            course_code=course_code,
            status="published",
            approved_by=actor.name,
            approved_by_id=actor.user_id,
            workspace_snapshot=final_workspace,
            metrics=metrics,
            human_edits=applied_edits,
        )

        # Store in version history
        self.version_history[course_id][next_v] = release
        self.active_versions[course_id] = next_v

        # Runtime audit provenance log
        self.runtime.log_step(
            run_id=release_id,
            agent_name="SafetyGovernanceManager",
            action="publish_approved_version",
            inputs={"course_id": course_id, "version": next_v, "approved_by": actor.name},
            outputs={"release_id": release_id, "average_score": metrics.average_score, "status": "published"},
        )

        return release

    # ── 3. One-Click Instant Rollback ─────────────────────────────────────────

    def rollback(
        self,
        course_id: int,
        target_version: int,
        actor: RoleContext
    ) -> RollbackResult:
        """
        Executes Chapter 2 pseudocode:
          on rollback(v): restore(version=v)
        Restores any historical version cleanly.
        """
        if not actor.can_approve:
            raise PermissionError(
                f"Unauthorized action: Actor '{actor.name}' cannot execute rollback. Faculty permission required."
            )

        course_versions = self.version_history.get(course_id, {})
        if target_version not in course_versions:
            raise ValueError(
                f"Cannot rollback to version v{target_version}: Version not found in history for course #{course_id}. "
                f"Available versions: {list(course_versions.keys())}"
            )

        target_release = course_versions[target_version]
        restored_snapshot = copy.deepcopy(target_release.workspace_snapshot)

        # Mark active version
        self.active_versions[course_id] = target_version

        # Runtime audit provenance log
        self.runtime.log_step(
            run_id=f"rollback_c{course_id}_v{target_version}",
            agent_name="SafetyGovernanceManager",
            action="rollback_version",
            inputs={"course_id": course_id, "target_version": target_version, "actor": actor.name},
            outputs={"restored_release_id": target_release.release_id, "status": "restored"},
        )

        return RollbackResult(
            course_id=course_id,
            target_version=target_version,
            restored_release_id=target_release.release_id,
            active_version=target_version,
            rolled_back_by=actor.name,
            restored_workspace=restored_snapshot,
        )

    # ── 4. Metrics Recording ──────────────────────────────────────────────────

    def _calculate_evaluation_metrics(
        self,
        workspace: Dict[str, Any],
        release_id: str,
        human_edits_count: int
    ) -> EvaluationMetrics:
        """Computes statistical metrics over published grades."""
        grades = workspace.get("grading_results", [])
        scores = [float(g.get("final_score", 0.0)) for g in grades if isinstance(g.get("final_score"), (int, float))]

        if scores:
            avg_score = round(statistics.mean(scores), 2)
            med_score = round(statistics.median(scores), 2)
            max_score = round(max(scores), 2)
            min_score = round(min(scores), 2)
        else:
            avg_score = med_score = max_score = min_score = 0.0

        distribution = {"A (90-100)": 0, "B (80-89)": 0, "C (70-79)": 0, "D (60-69)": 0, "F (<60)": 0}
        for s in scores:
            if s >= 90:
                distribution["A (90-100)"] += 1
            elif s >= 80:
                distribution["B (80-89)"] += 1
            elif s >= 70:
                distribution["C (70-79)"] += 1
            elif s >= 60:
                distribution["D (60-69)"] += 1
            else:
                distribution["F (<60)"] += 1

        quarantined = sum(1 for g in grades if g.get("held_for_plagiarism", False))
        submissions = workspace.get("submissions", [])
        late_count = sum(1 for s in submissions if s.get("late_penalty_applied", False))

        return EvaluationMetrics(
            release_id=release_id,
            total_submissions=len(submissions),
            average_score=avg_score,
            median_score=med_score,
            highest_score=max_score,
            lowest_score=min_score,
            grade_distribution=distribution,
            plagiarism_quarantine_count=quarantined,
            late_penalty_count=late_count,
            human_edits_count=human_edits_count,
        )
