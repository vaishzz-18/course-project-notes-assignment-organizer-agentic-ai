"""Lab 3 — Format skill: renders structured output into human-readable documents."""
import json
from typing import List, Optional
from datetime import datetime


def format_grade_report(submission_id: int, student_name: str, assignment_title: str,
                         draft_marks: float, max_marks: float, feedback: str,
                         rubric_breakdown: dict, similarity_score: Optional[float] = None) -> str:
    lines = [
        f"GRADE REPORT — {assignment_title}",
        f"Student: {student_name} | Submission ID: {submission_id}",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 60,
        f"Draft Score: {draft_marks} / {max_marks}  ({100*draft_marks/max_marks:.1f}%)",
        "",
        "RUBRIC BREAKDOWN",
        "-" * 40,
    ]
    for criterion, detail in rubric_breakdown.items():
        lines.append(f"  {criterion}: {detail.get('marks', '?')} / {detail.get('max', '?')}")
        if detail.get("comment"):
            lines.append(f"    ↳ {detail['comment']}")

    lines += ["", "FEEDBACK", "-" * 40, feedback]

    if similarity_score is not None:
        flag = " ⚠ HIGH — flagged for review" if similarity_score > 0.75 else ""
        lines += ["", f"Similarity Score: {similarity_score:.0%}{flag}"]

    lines += ["", "— Draft only. Awaiting faculty approval. —"]
    return "\n".join(lines)


def format_submission_dashboard(assignment_title: str, rows: List[dict]) -> str:
    lines = [
        f"SUBMISSION DASHBOARD — {assignment_title}",
        f"Total: {len(rows)}",
        "-" * 70,
        f"{'Student':<25} {'Submitted':<22} {'Status':<10} {'Similarity':>10}",
        "-" * 70,
    ]
    for r in rows:
        sim = f"{r.get('similarity_score', 0):.0%}" if r.get("similarity_score") is not None else "—"
        late = " LATE" if r.get("is_late") else ""
        lines.append(
            f"{r['student_name']:<25} {r['submitted_at']:<22} {late or 'on-time':<10} {sim:>10}"
        )
    return "\n".join(lines)


def format_milestone_report(course_name: str, rows: List[dict]) -> str:
    lines = [
        f"MILESTONE TRACKER — {course_name}",
        "-" * 70,
        f"{'Group':<25} {'Milestone':<30} {'Health':<8} {'Status'}",
        "-" * 70,
    ]
    for r in rows:
        health_icon = {"green": "✓", "amber": "!", "red": "✗"}.get(r.get("health", "green"), "?")
        lines.append(
            f"{r['group_name']:<25} {r['milestone_title']:<30} {health_icon:<8} {r['status']}"
        )
    return "\n".join(lines)
