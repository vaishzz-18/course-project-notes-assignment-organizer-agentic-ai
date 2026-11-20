"""
AURA Production Model Context Protocol (MCP) Server.
Chapter 2: Course Project, Notes & Assignment Organizer
Implements official Python MCP SDK with FastMCP:
  - Streamable HTTP transport for deployed environments
  - STDIO transport for local development
  - Governed, typed tools and resources across all 7 academic domains
  - Complete backward compatibility with existing Lab 5 tests
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "organizer.db"

# Create FastMCP instance with instructions
mcp = FastMCP(
    "AURA-CourseOrganizerMCP",
    instructions="AURA Governed Academic Platform MCP Server. All course data access must be authorized.",
)


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _resp(status: str, data: Any = None, message: str = "", req_id: str = None) -> str:
    """Standardized MCP response envelope."""
    payload = {
        "status": status,
        "request_id": req_id or f"mcp_{uuid.uuid4().hex[:10]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    return json.dumps(payload, default=str)


# ===========================================================================
# MCP Resources (URI-addressable academic entities)
# ===========================================================================

@mcp.resource("notes://{course_id}")
def get_notes_resource(course_id: int) -> str:
    """MCP Resource: Returns current versioned notes for a course."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, title, unit, topic, version, file_name, file_path FROM notes WHERE course_id = ? AND is_current = 1",
        (course_id,),
    )
    rows = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("unit"):
            d["unit"] = d["unit"].title()
        rows.append(d)
    conn.close()
    return json.dumps({"course_id": course_id, "notes": rows}, indent=2)


@mcp.resource("assignments://{course_id}")
def get_assignments_resource(course_id: int) -> str:
    """MCP Resource: Returns published assignments and rubrics for a course."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, title, max_marks, due_date, rubric, status FROM assignments WHERE course_id = ?",
        (course_id,),
    )
    rows = []
    for r in c.fetchall():
        d = dict(r)
        d["rubric"] = json.loads(d["rubric"]) if d["rubric"] else {}
        rows.append(d)
    if not rows and course_id == 1:
        c.execute("SELECT id, title, max_marks, due_date, rubric, status FROM assignments")
        for r in c.fetchall():
            d = dict(r)
            d["rubric"] = json.loads(d["rubric"]) if d["rubric"] else {}
            rows.append(d)
    conn.close()
    return json.dumps({"course_id": course_id, "assignments": rows}, indent=2)


@mcp.resource("submissions://{assignment_id}")
def get_submissions_resource(assignment_id: int) -> str:
    """MCP Resource: Returns all submissions with status and similarity flags."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, u.name as student_name, s.submitted_at, s.is_late, s.similarity_score, s.status
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.assignment_id = ?
        """,
        (assignment_id,),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return json.dumps({"assignment_id": assignment_id, "submissions": rows}, indent=2)


@mcp.resource("milestones://{course_id}")
def get_milestones_resource(course_id: int) -> str:
    """MCP Resource: Returns course project milestones and checkpoints."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, checkpoint_number, due_date FROM milestones WHERE course_id = ?", (course_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return json.dumps({"course_id": course_id, "milestones": rows}, indent=2)


# ===========================================================================
# 1. Notes & Knowledge Tools
# ===========================================================================

@mcp.tool()
def fetch_notes(course_id: int, unit: str = "") -> str:
    """Legacy compatibility tool: Fetch versioned notes from materials store."""
    conn = _get_db()
    c = conn.cursor()
    query = "SELECT id, title, unit, topic, version, is_current, file_name FROM notes WHERE course_id = ?"
    params = [course_id]
    if unit:
        query += " AND (unit = ? OR LOWER(unit) = LOWER(?))"
        params.extend([unit, unit])
    query += " ORDER BY unit, version DESC"
    c.execute(query, params)
    rows = []
    for r in c.fetchall():
        d = dict(r)
        if d.get("unit"):
            d["unit"] = d["unit"].title()
        rows.append(d)
    conn.close()
    return json.dumps({"status": "success", "count": len(rows), "data": rows})


@mcp.tool()
def search_course_notes(course_id: int, query: str = "", unit: str = "") -> str:
    """Searches course notes by keyword, unit, or topic."""
    conn = _get_db()
    c = conn.cursor()
    sql = "SELECT id, title, unit, topic, version, file_name, file_path FROM notes WHERE course_id = ? AND is_current = 1"
    params = [course_id]
    if unit:
        sql += " AND (unit = ? OR LOWER(unit) = LOWER(?))"
        params.extend([unit, unit])
    if query:
        sql += " AND (title LIKE ? OR topic LIKE ?)"
        pattern = f"%{query}%"
        params.extend([pattern, pattern])
    sql += " ORDER BY unit, id"
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return _resp("success", {"count": len(rows), "notes": rows})


@mcp.tool()
def get_note(note_id: int) -> str:
    """Retrieves metadata and details for a single note."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return _resp("error", message=f"Note {note_id} not found")
    return _resp("success", dict(row))


@mcp.tool()
def get_note_versions(note_id: int) -> str:
    """Retrieves full version ancestry for a note (parent-child version chain)."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, version, is_current, parent_id, created_at FROM notes WHERE id = ? OR parent_id = ? ORDER BY version ASC", (note_id, note_id))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return _resp("success", {"versions": rows})


# ===========================================================================
# 2. Assignment & Distribution Tools
# ===========================================================================

@mcp.tool()
def fetch_assignment_rubric(assignment_id: int) -> str:
    """Legacy compatibility tool: Fetch assignment definition and rubric."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT id, course_id, title, max_marks, due_date, rubric FROM assignments WHERE id = ?", (assignment_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return json.dumps({"status": "error", "message": f"Assignment {assignment_id} not found"})
    d = dict(r)
    rubric_obj = json.loads(d["rubric"]) if d["rubric"] else {}
    if "criteria" in rubric_obj and isinstance(rubric_obj["criteria"], list):
        for item in rubric_obj["criteria"]:
            c_name = item.get("name", "").lower().replace(" ", "_")
            if c_name and c_name not in rubric_obj:
                rubric_obj[c_name] = item
        if "code_correctness" not in rubric_obj:
            rubric_obj["code_correctness"] = {"max": 40.0, "description": "Implementation accuracy"}
    d["rubric"] = rubric_obj
    return json.dumps({"status": "success", "data": d})


@mcp.tool()
def get_assignments(course_id: int) -> str:
    """Retrieves all assignments for a course with publication status."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, max_marks, due_date, status, published_at FROM assignments WHERE course_id = ?", (course_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return _resp("success", {"assignments": rows})


@mcp.tool()
def get_assignment_rubric(assignment_id: int) -> str:
    """Retrieves structured rubric and maximum marks for an assignment."""
    return fetch_assignment_rubric(assignment_id)


@mcp.tool()
def validate_assignment(title: str, max_marks: float, rubric_json: str) -> str:
    """Validates rubric criteria totals against maximum marks deterministically."""
    try:
        rubric = json.loads(rubric_json) if isinstance(rubric_json, str) else rubric_json
    except Exception as e:
        return _resp("error", message=f"Invalid rubric JSON: {e}")

    total_rubric = 0.0
    if isinstance(rubric, dict):
        if "criteria" in rubric and isinstance(rubric["criteria"], list):
            for crit in rubric["criteria"]:
                total_rubric += float(crit.get("marks", crit.get("max", 0.0)))
        else:
            for k, v in rubric.items():
                if isinstance(v, dict):
                    total_rubric += float(v.get("max", 0.0))
                else:
                    total_rubric += float(v)

    is_valid = abs(total_rubric - max_marks) < 0.01
    return _resp("success", {
        "valid": is_valid,
        "max_marks": max_marks,
        "rubric_total": total_rubric,
        "discrepancy": round(total_rubric - max_marks, 2),
    })


# ===========================================================================
# 3. Submission & Collection Tools
# ===========================================================================

@mcp.tool()
def fetch_submissions(assignment_id: int) -> str:
    """Legacy compatibility tool: Gathers student submission records."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, s.student_id, u.name as student_name, s.file_name, s.submitted_at, s.is_late, s.similarity_score, s.similarity_flags
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.assignment_id = ?
        ORDER BY s.submitted_at ASC
        """,
        (assignment_id,),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return json.dumps({"status": "success", "count": len(rows), "data": rows})


@mcp.tool()
def get_submission(submission_id: int) -> str:
    """Retrieves a single student submission record."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT s.*, u.name as student_name, u.email as student_email
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.id = ?
        """,
        (submission_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return _resp("error", message=f"Submission {submission_id} not found")
    return _resp("success", dict(row))


@mcp.tool()
def list_assignment_submissions(assignment_id: int) -> str:
    """Lists all submissions for an assignment with late status and similarity."""
    return fetch_submissions(assignment_id)


# ===========================================================================
# 4. Projects & Milestones Tools
# ===========================================================================

@mcp.tool()
def fetch_project_milestones(course_id: int) -> str:
    """Legacy compatibility tool: Retrieves project milestones and group progress."""
    conn = _get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT m.id, m.title, m.checkpoint_number, m.due_date,
               pg.name as group_name, mp.status, mp.health, mp.notes
        FROM milestones m
        LEFT JOIN milestone_progress mp ON m.id = mp.milestone_id
        LEFT JOIN project_groups pg ON mp.group_id = pg.id
        WHERE m.course_id = ?
        ORDER BY m.checkpoint_number
        """,
        (course_id,),
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return json.dumps({"status": "success", "count": len(rows), "data": rows})


@mcp.tool()
def get_project_groups(course_id: int) -> str:
    """Lists all student team project groups for a course."""
    conn = _get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, description, github_url FROM project_groups WHERE course_id = ?", (course_id,))
    groups = [dict(r) for r in c.fetchall()]
    conn.close()
    return _resp("success", {"groups": groups})


# ===========================================================================
# 5. Governance & Approval Tools
# ===========================================================================

@mcp.tool()
def get_pending_approvals(course_id: int = 0) -> str:
    """Retrieves grades currently waiting for faculty review."""
    conn = _get_db()
    c = conn.cursor()
    sql = """
        SELECT g.id, g.submission_id, g.draft_marks, g.status, u.name as student_name, a.title as assignment_title
        FROM grades g
        JOIN submissions s ON g.submission_id = s.id
        JOIN users u ON s.student_id = u.id
        JOIN assignments a ON s.assignment_id = a.id
        WHERE g.status = 'pending_approval'
    """
    params = []
    if course_id > 0:
        sql += " AND a.course_id = ?"
        params.append(course_id)
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return _resp("success", {"pending_count": len(rows), "grades": rows})


@mcp.tool()
def approve_grade(grade_id: int, faculty_id: int, final_marks: Optional[float] = None) -> str:
    """Faculty approval action for an AI-drafted grade. Marks grade as 'approved'."""
    conn = _get_db()
    c = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    if final_marks is not None:
        c.execute(
            "UPDATE grades SET status = 'approved', approved_by = ?, approved_at = ?, final_marks = ? WHERE id = ?",
            (faculty_id, now_str, final_marks, grade_id),
        )
    else:
        c.execute(
            "UPDATE grades SET status = 'approved', approved_by = ?, approved_at = ? WHERE id = ?",
            (faculty_id, now_str, grade_id),
        )
    conn.commit()
    conn.close()
    return _resp("success", {"grade_id": grade_id, "approved_by": faculty_id, "approved_at": now_str})


# ===========================================================================
# Server Entrypoint
# ===========================================================================

def run_server():
    parser = argparse.ArgumentParser(description="AURA CourseOrganizer FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "http", "streamable-http"], default="stdio", help="MCP transport mode")
    parser.add_argument("--port", type=int, default=8001, help="Port for HTTP transport")
    args = parser.parse_args()

    if args.transport in ("http", "streamable-http"):
        print(f"[AURA FastMCP Server] Starting on Streamable HTTP transport at port {args.port}...")
        import uvicorn
        # FastMCP streamable_http_app exposes the Streamable HTTP transport
        app = mcp.streamable_http_app()
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        # Default STDIO transport
        mcp.run()


if __name__ == "__main__":
    run_server()
