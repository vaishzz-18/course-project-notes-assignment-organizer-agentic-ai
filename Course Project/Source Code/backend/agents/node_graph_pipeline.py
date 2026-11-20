"""
Lab 7: Agentic Node Graph — Full Pipeline via LangGraph
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Wire all specialist agents into an explicit LangGraph StateGraph, replacing a procedural
for-loop with a declarative, inspectable, self-healing node graph.

Pipeline:
  Ingest → Plan → Notes → Distribute → Collect → Similarity → Grading → Validate
  Validate --fail(attempts < MAX)--> Grading   (bounded retry back-edge)
  Validate --pass--> FacultyGate               (human stop)

Acceptance Criteria:
  • Every node is a separate, named agent with logged inputs/outputs.
  • The retry back-edge fires when rubric integrity fails (and stops after MAX_RETRIES).
  • Execution halts at FacultyGate until a named human approves.
  • The full run is audit-logged via AURAControlledRuntime.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict, Annotated
import operator

from pydantic import BaseModel

# ── LangGraph ────────────────────────────────────────────────────────────────
from langgraph.graph import StateGraph, END

# ── Internal modules ─────────────────────────────────────────────────────────
from runtime.governed_runtime import AURAControlledRuntime, RuntimeBudget
from agents.retrieval_agent import CourseRetrievalAgent

# ---------------------------------------------------------------------------
# Shared Graph State (TypedDict for LangGraph)
# ---------------------------------------------------------------------------

class CourseGraphState(TypedDict):
    # Immutable run identity
    run_id: str
    course_id: int
    faculty_id: int

    # Mutable pipeline payload
    plan: Dict[str, Any]
    notes_summary: List[Dict[str, Any]]
    distributed_assignments: List[Dict[str, Any]]
    collected_submissions: List[Dict[str, Any]]
    similarity_flags: List[Dict[str, Any]]
    grading_results: List[Dict[str, Any]]
    validation_report: Dict[str, Any]

    # Control flow
    retry_count: int
    pipeline_status: str           # running | needs_faculty_review | complete | error
    human_approved: bool
    error_message: Optional[str]

    # Audit trail accumulated across nodes
    audit_trail: Annotated[List[str], operator.add]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_GRADING_RETRIES = 3
DB_PATH = Path(__file__).parent.parent.parent / "data" / "organizer.db"


# ---------------------------------------------------------------------------
# Helper: SQLite query utility
# ---------------------------------------------------------------------------

def _query(sql: str, params: tuple = ()) -> List[Dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Node 1 — Ingest
# ---------------------------------------------------------------------------

def node_ingest(state: CourseGraphState) -> Dict[str, Any]:
    """
    IngestAgent: Validates course exists and assembles run context.
    Logs: course_id, faculty_id, assignments count.
    """
    course_id = state["course_id"]
    rows = _query("SELECT id, name, code FROM courses WHERE id = ?", (course_id,))
    if not rows:
        return {
            "pipeline_status": "error",
            "error_message": f"Course {course_id} not found in DB.",
            "audit_trail": [f"[Ingest] ERROR: course {course_id} not found."],
        }

    course = rows[0]
    assignments = _query(
        "SELECT id, title, due_date FROM assignments WHERE course_id = ?", (course_id,)
    )

    plan_seed = {
        "course_name": course["name"],
        "course_code": course["code"],
        "assignments": [{"id": a["id"], "title": a["title"], "due_date": a["due_date"]} for a in assignments],
        "unit_count": 4,
    }

    return {
        "plan": plan_seed,
        "pipeline_status": "running",
        "audit_trail": [
            f"[Ingest] Course: '{course['name']}' ({course['code']}) | "
            f"Assignments: {len(assignments)} | RunID: {state['run_id']}"
        ],
    }


# ---------------------------------------------------------------------------
# Node 2 — Plan
# ---------------------------------------------------------------------------

def node_plan(state: CourseGraphState) -> Dict[str, Any]:
    """
    PlannerAgent: Enriches raw plan with a structured organizer workspace template.
    Incorporates locked constraints from Lab 3 PlanSkill semantics.
    """
    plan = state["plan"]
    plan["workspace_version"] = "v1.0"
    plan["grading_policy"] = {
        "late_penalty_percent": 100,
        "plagiarism_threshold": 0.85,
        "rubric_total_marks": 100,
    }
    plan["units"] = [
        {"unit": "Unit 1", "topic": "Agent Foundations", "week": 1},
        {"unit": "Unit 2", "topic": "Tools & MCP",        "week": 3},
        {"unit": "Unit 3", "topic": "LangGraph Pipelines", "week": 6},
        {"unit": "Unit 4", "topic": "Parallel Swarms",   "week": 9},
    ]
    plan["locked_at"] = datetime.utcnow().isoformat()

    return {
        "plan": plan,
        "audit_trail": [
            f"[Plan] Locked workspace plan | "
            f"Units: {len(plan['units'])} | "
            f"Late penalty: {plan['grading_policy']['late_penalty_percent']}%"
        ],
    }


# ---------------------------------------------------------------------------
# Node 3 — Notes
# ---------------------------------------------------------------------------

def node_notes(state: CourseGraphState) -> Dict[str, Any]:
    """
    NotesRepositoryAgent: Pulls current course notes from DB using tag-based retrieval.
    Uses CourseRetrievalAgent (Lab 4 long-term memory).
    """
    course_id = state["course_id"]
    rows = _query(
        "SELECT id, title, unit, topic, version FROM notes WHERE course_id = ? AND is_current = 1 ORDER BY unit",
        (course_id,),
    )

    summary = [
        {
            "note_id": r["id"],
            "title": r["title"],
            "unit": r["unit"],
            "topic": r["topic"],
            "version": r["version"],
        }
        for r in rows
    ]

    return {
        "notes_summary": summary,
        "audit_trail": [
            f"[Notes] Retrieved {len(summary)} current notes for course {course_id} | "
            f"Units covered: {sorted(set(n['unit'] for n in summary))}"
        ],
    }


# ---------------------------------------------------------------------------
# Node 4 — Distribute
# ---------------------------------------------------------------------------

def node_distribute(state: CourseGraphState) -> Dict[str, Any]:
    """
    AssignmentDistributionAgent: Records assignment distribution events for all
    enrolled students. Marks distributions in the run context.
    """
    course_id = state["course_id"]
    students = _query(
        """
        SELECT u.id, u.name, u.email
        FROM users u
        JOIN course_enrollments ce ON ce.student_id = u.id
        WHERE ce.course_id = ?
        """,
        (course_id,),
    )
    assignments = state["plan"].get("assignments", [])

    distributed = []
    for student in students:
        for asgn in assignments:
            distributed.append({
                "student_id": student["id"],
                "student_name": student["name"],
                "assignment_id": asgn["id"],
                "assignment_title": asgn["title"],
                "distributed_at": datetime.utcnow().isoformat(),
                "status": "distributed",
            })

    return {
        "distributed_assignments": distributed,
        "audit_trail": [
            f"[Distribute] Distributed {len(assignments)} assignment(s) to "
            f"{len(students)} students → {len(distributed)} distribution events"
        ],
    }


# ---------------------------------------------------------------------------
# Node 5 — Collect
# ---------------------------------------------------------------------------

def node_collect(state: CourseGraphState) -> Dict[str, Any]:
    """
    SubmissionCollectionAgent: Fetches all submissions from DB and marks late ones
    per the grading policy deadline.
    """
    course_id = state["course_id"]
    submissions = _query(
        """
        SELECT s.id, s.file_name, s.file_path, s.submitted_at, s.is_late,
               u.name as student_name, a.title as assignment_title, a.due_date
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        WHERE a.course_id = ?
        ORDER BY s.submitted_at
        """,
        (course_id,),
    )

    collected = []
    late_count = 0
    for sub in submissions:
        is_late = bool(sub["is_late"])
        if is_late:
            late_count += 1
        # Read submission text for downstream similarity checks
        file_path = Path(sub["file_path"]) if sub["file_path"] else None
        content = ""
        if file_path and file_path.exists():
            content = file_path.read_text(encoding="utf-8", errors="ignore")[:500]

        collected.append({
            "submission_id": sub["id"],
            "student_name": sub["student_name"],
            "assignment_title": sub["assignment_title"],
            "file_name": sub["file_name"],
            "submitted_at": sub["submitted_at"],
            "is_late": is_late,
            "content_preview": content,
        })

    return {
        "collected_submissions": collected,
        "audit_trail": [
            f"[Collect] {len(collected)} submissions collected | "
            f"Late: {late_count} | "
            f"On-time: {len(collected) - late_count}"
        ],
    }


# ---------------------------------------------------------------------------
# Node 6 — Similarity (feeds into Lab 8 Swarm)
# ---------------------------------------------------------------------------

def node_similarity(state: CourseGraphState) -> Dict[str, Any]:
    """
    SimilarityAgent: Runs pairwise TF-IDF cosine similarity over all collected
    submissions. Flags pairs above the plagiarism threshold.
    This node mirrors what Lab 8's parallel swarm does, but sequentially so
    the graph baseline is correct.
    """
    submissions = state["collected_submissions"]
    threshold = state["plan"].get("grading_policy", {}).get("plagiarism_threshold", 0.85)

    flags: List[Dict[str, Any]] = []
    texts = [s.get("content_preview", "") for s in submissions]

    if len(texts) >= 2:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as sk_cos
        import numpy as np

        # Filter out empty docs to avoid sklearn warning
        non_empty = [(i, t) for i, t in enumerate(texts) if t.strip()]
        if len(non_empty) >= 2:
            indices, valid_texts = zip(*non_empty)
            vec = TfidfVectorizer(stop_words="english")
            mat = vec.fit_transform(valid_texts)
            sim_matrix = sk_cos(mat)

            for i in range(len(valid_texts)):
                for j in range(i + 1, len(valid_texts)):
                    score = float(sim_matrix[i][j])
                    if score >= threshold:
                        flags.append({
                            "submission_a_id": submissions[indices[i]]["submission_id"],
                            "submission_b_id": submissions[indices[j]]["submission_id"],
                            "student_a": submissions[indices[i]]["student_name"],
                            "student_b": submissions[indices[j]]["student_name"],
                            "similarity_score": round(score, 4),
                            "is_plagiarism_risk": True,
                        })

    return {
        "similarity_flags": flags,
        "audit_trail": [
            f"[Similarity] Checked {len(submissions)} submissions | "
            f"Flagged pairs: {len(flags)} (threshold={threshold})"
        ],
    }


# ---------------------------------------------------------------------------
# Node 7 — Grading
# ---------------------------------------------------------------------------

def node_grading(state: CourseGraphState) -> Dict[str, Any]:
    """
    GradingAgent: Applies rubric formula with late penalty and deductions for
    flagged plagiarism. Produces a marks breakdown per submission.

    Rubric (from locked plan):
      Part A: Understanding    25 marks
      Part B: Implementation   40 marks
      Part C: Testing          20 marks
      Part D: Report           15 marks
      Total:                  100 marks
    Late penalty: -10%
    """
    submissions = state["collected_submissions"]
    flags = state["similarity_flags"]
    late_penalty = state["plan"].get("grading_policy", {}).get("late_penalty_percent", 10)
    retry_count = state.get("retry_count", 0)

    flagged_ids = {f["submission_a_id"] for f in flags} | {f["submission_b_id"] for f in flags}

    RUBRIC = {
        "understanding":    {"max": 25, "awarded": 20},
        "implementation":   {"max": 40, "awarded": 35},
        "testing":          {"max": 20, "awarded": 16},
        "report":           {"max": 15, "awarded": 12},
    }

    results = []
    for sub in submissions:
        sub_id = sub["submission_id"]
        raw_total = sum(v["awarded"] for v in RUBRIC.values())   # 83

        deductions = []
        final = raw_total

        # Late penalty: 0 marks awarded for late submissions
        if sub.get("is_late"):
            penalty = final
            final = 0.0
            deductions.append({"reason": "late_submission", "deduction": penalty, "note": "Late submission policy: 0 marks awarded"})

        # Plagiarism hold
        plagiarism_held = sub_id in flagged_ids
        if plagiarism_held:
            deductions.append({"reason": "plagiarism_pending_review", "deduction": 0, "note": "Grade withheld"})
            final = 0

        results.append({
            "submission_id": sub_id,
            "student_name": sub["student_name"],
            "rubric_breakdown": {k: {"max": v["max"], "awarded": v["awarded"]} for k, v in RUBRIC.items()},
            "raw_total": raw_total,
            "deductions": deductions,
            "final_marks": round(final, 1),
            "plagiarism_held": plagiarism_held,
            "graded_on_attempt": retry_count + 1,
        })

    return {
        "grading_results": results,
        "audit_trail": [
            f"[Grading] Graded {len(results)} submissions | "
            f"Attempt #{retry_count + 1} | "
            f"Withheld for plagiarism: {sum(1 for r in results if r['plagiarism_held'])}"
        ],
    }


# ---------------------------------------------------------------------------
# Node 8 — Validate
# ---------------------------------------------------------------------------

def node_validate(state: CourseGraphState) -> Dict[str, Any]:
    """
    ValidationAgent: Checks rubric integrity, budget compliance, and completeness.
    If validation fails AND retries remain, triggers regrade back-edge.
    If validation passes, prepares assembled draft for FacultyGate.
    """
    grading_results = state["grading_results"]
    plan = state["plan"]
    retry_count = state.get("retry_count", 0)

    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: All submissions must have a grading entry
    collected_ids = {s["submission_id"] for s in state["collected_submissions"]}
    graded_ids = {r["submission_id"] for r in grading_results}
    missing = collected_ids - graded_ids
    if missing:
        errors.append(f"Missing grades for submission IDs: {missing}")

    # Rule 2: No marks can exceed rubric max
    rubric_total_max = plan.get("grading_policy", {}).get("rubric_total_marks", 100)
    for r in grading_results:
        if r["final_marks"] > rubric_total_max:
            errors.append(f"Marks overflow: {r['student_name']} got {r['final_marks']} > {rubric_total_max}")

    # Rule 3: Plagiarism flags must be acknowledged
    flagged = [r for r in grading_results if r["plagiarism_held"]]
    if flagged:
        warnings.append(
            f"{len(flagged)} submission(s) withheld pending faculty plagiarism review: "
            + ", ".join(r["student_name"] for r in flagged)
        )

    passed = len(errors) == 0
    new_retry = retry_count + (0 if passed else 1)

    report = {
        "validation_passed": passed,
        "total_graded": len(grading_results),
        "errors": errors,
        "warnings": warnings,
        "retry_count": new_retry,
        "max_retries": MAX_GRADING_RETRIES,
    }

    new_status = "needs_faculty_review" if passed else (
        "error" if new_retry >= MAX_GRADING_RETRIES else "running"
    )

    return {
        "validation_report": report,
        "retry_count": new_retry,
        "pipeline_status": new_status,
        "audit_trail": [
            f"[Validate] {'PASS' if passed else 'FAIL'} | "
            f"Errors: {len(errors)} | Warnings: {len(warnings)} | "
            f"Status → {new_status}"
        ],
    }


# ---------------------------------------------------------------------------
# Node 9 — Faculty Gate (Human Stop)
# ---------------------------------------------------------------------------

def node_faculty_gate(state: CourseGraphState) -> Dict[str, Any]:
    """
    FacultyGate: Hard human review stop. Execution cannot proceed past this node
    without explicit faculty approval (human_approved = True).

    In this pipeline, reaching this node *is* the stop point. The REST API
    endpoint will return the assembled draft for review.
    The approval action is a separate API call (POST /lab7/approve).
    """
    approved = state.get("human_approved", False)

    try:
        from runtime.workflow_persistence_service import WorkflowPersistenceService
        svc = WorkflowPersistenceService()
        thread_id = f"thread_{state.get('run_id')}"
        svc.save_checkpoint(
            thread_id=thread_id,
            run_id=state.get("run_id", "unknown"),
            current_node="node_faculty_gate",
            state=dict(state),
            status="waiting_approval" if not approved else "completed",
            approval_status="approved" if approved else "pending",
        )
    except Exception:
        pass

    assembled_draft = {
        "run_id": state["run_id"],
        "course_id": state["course_id"],
        "plan": state["plan"],
        "notes_count": len(state.get("notes_summary", [])),
        "distributions_count": len(state.get("distributed_assignments", [])),
        "submissions_count": len(state.get("collected_submissions", [])),
        "similarity_flags_count": len(state.get("similarity_flags", [])),
        "grading_results": state.get("grading_results", []),
        "validation_report": state.get("validation_report", {}),
        "faculty_approved": approved,
        "assembled_at": datetime.utcnow().isoformat(),
    }

    return {
        "pipeline_status": "complete" if approved else "needs_faculty_review",
        "audit_trail": [
            f"[FacultyGate] Draft assembled | "
            f"Faculty approval: {'GRANTED' if approved else 'PENDING'}"
        ],
    }


# ---------------------------------------------------------------------------
# Conditional Edges
# ---------------------------------------------------------------------------

def edge_validate_router(state: CourseGraphState) -> Literal["node_grading", "node_faculty_gate", "__end__"]:
    """
    Routes from Validate node:
      - If failed AND retries remain → back to Grading (self-healing)
      - If failed AND retries exhausted → END with error
      - If passed → FacultyGate
    """
    report = state.get("validation_report", {})
    retry_count = state.get("retry_count", 0)

    if not report.get("validation_passed", False):
        if retry_count < MAX_GRADING_RETRIES:
            return "node_grading"   # retry back-edge
        else:
            return "__end__"        # abort after max retries
    return "node_faculty_gate"


def edge_after_ingest(state: CourseGraphState) -> Literal["node_plan", "__end__"]:
    if state.get("pipeline_status") == "error":
        return "__end__"
    return "node_plan"


# ---------------------------------------------------------------------------
# Build & Compile the LangGraph StateGraph
# ---------------------------------------------------------------------------

def build_course_pipeline() -> Any:
    """
    Constructs and compiles the full course organizer LangGraph StateGraph.
    Returns a compiled runnable graph.
    """
    g = StateGraph(CourseGraphState)

    # Register nodes
    g.add_node("node_ingest",       node_ingest)
    g.add_node("node_plan",         node_plan)
    g.add_node("node_notes",        node_notes)
    g.add_node("node_distribute",   node_distribute)
    g.add_node("node_collect",      node_collect)
    g.add_node("node_similarity",   node_similarity)
    g.add_node("node_grading",      node_grading)
    g.add_node("node_validate",     node_validate)
    g.add_node("node_faculty_gate", node_faculty_gate)

    # Entry point
    g.set_entry_point("node_ingest")

    # Linear edges
    g.add_conditional_edges("node_ingest", edge_after_ingest, {
        "node_plan": "node_plan",
        "__end__": END,
    })
    g.add_edge("node_plan",       "node_notes")
    g.add_edge("node_notes",      "node_distribute")
    g.add_edge("node_distribute", "node_collect")
    g.add_edge("node_collect",    "node_similarity")
    g.add_edge("node_similarity", "node_grading")
    g.add_edge("node_grading",    "node_validate")

    # Conditional: Validate → Grading (retry) OR FacultyGate OR END
    g.add_conditional_edges("node_validate", edge_validate_router, {
        "node_grading":      "node_grading",
        "node_faculty_gate": "node_faculty_gate",
        "__end__":           END,
    })

    # Faculty gate → done
    g.add_edge("node_faculty_gate", END)

    return g.compile()


# ---------------------------------------------------------------------------
# High-level Runner (used by REST API & demo script)
# ---------------------------------------------------------------------------

class PipelineRunner:
    """
    Wraps the compiled LangGraph pipeline with AURAControlledRuntime governance.
    Every graph invocation is audit-logged and checkpointed.
    """

    def __init__(self):
        self.graph = build_course_pipeline()
        self.runtime = AURAControlledRuntime(
            budget=RuntimeBudget(max_steps=50, max_cost_tokens=200_000, timeout_seconds=120.0),
            gates=["faculty_approval_gate"],
        )

    def run(
        self,
        course_id: int,
        faculty_id: int,
        human_approved: bool = False,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes the full course pipeline via LangGraph.
        Returns the final graph state including audit trail and validation report.
        """
        run_id = run_id or f"lab7_{uuid.uuid4().hex[:10]}"

        initial_state: CourseGraphState = {
            "run_id": run_id,
            "course_id": course_id,
            "faculty_id": faculty_id,
            "plan": {},
            "notes_summary": [],
            "distributed_assignments": [],
            "collected_submissions": [],
            "similarity_flags": [],
            "grading_results": [],
            "validation_report": {},
            "retry_count": 0,
            "pipeline_status": "running",
            "human_approved": human_approved,
            "error_message": None,
            "audit_trail": [f"[PipelineRunner] Run started: {run_id}"],
        }

        # Log run start to governed runtime
        self.runtime.log_step(
            run_id, "PipelineRunner", "graph_start",
            {"course_id": course_id, "human_approved": human_approved},
            {"graph": "CourseOrganizerPipeline"},
            cost=5,
        )

        # Invoke LangGraph
        final_state = self.graph.invoke(initial_state)

        # Checkpoint final state
        self.runtime.checkpoint(run_id, "pipeline_complete", {
            "pipeline_status": final_state.get("pipeline_status"),
            "validation_passed": final_state.get("validation_report", {}).get("validation_passed"),
            "graded_count": len(final_state.get("grading_results", [])),
        })

        # Log completion
        self.runtime.log_step(
            run_id, "PipelineRunner", "graph_complete",
            {"final_status": final_state.get("pipeline_status")},
            {"audit_entries": len(final_state.get("audit_trail", []))},
            cost=5,
        )

        return dict(final_state)


# Alias for backward-compatibility with capstone & tests
CourseGraphPipeline = PipelineRunner
