"""
AURA Governed MCP Connector Client.
Chapter 2: Course Project, Notes & Assignment Organizer
One unified, typed connector surface used by all agents.
No agent touches the database or raw filesystem directly;
every access is routed through the governed MCP protocol layer with audit logging.
"""
from typing import Dict, Any, List, Optional
import json
import time
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.course_mcp_server import (
    fetch_notes,
    fetch_assignment_rubric,
    fetch_submissions,
    fetch_project_milestones,
    search_course_notes,
    get_note,
    get_note_versions,
    get_assignments,
    validate_assignment,
    get_submission,
    get_project_groups,
    get_pending_approvals,
    approve_grade,
    get_notes_resource,
    get_assignments_resource,
    get_submissions_resource,
    get_milestones_resource,
    mcp,
)
from config import settings


class GovernedMCPConnectorClient:
    """
    Governed MCP Connector:
    The single governed surface for all course data.
    Agents interact exclusively through this connector interface.
    """

    CONNECTOR_NAME = "GovernedMCPConnectorClient"
    PROTOCOL_VERSION = "2024-11-05 (MCP)"

    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token or settings.MCP_AUTH_TOKEN or "auth-valid-token-agentic-aura"
        self.audit_log: List[Dict[str, Any]] = []

    def _log_mcp_access(
        self,
        action: str,
        target: str,
        status: str,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.audit_log.append({
            "action": action,
            "target": target,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "governed_by": self.CONNECTOR_NAME,
            "metadata": metadata or {},
        })

    def _verify_auth(self):
        """Validates that a non-empty auth token is present."""
        if not self.auth_token or not self.auth_token.strip():
            raise PermissionError("MCP Access Denied: Missing or empty authentication token")

    # ── Read 'the notes/materials store' ──────────────────────────────────────

    def read_notes_store(self, course_id: int, unit: str = "") -> List[Dict[str, Any]]:
        """Invokes MCP Tool: fetch_notes."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = fetch_notes(course_id=course_id, unit=unit)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "fetch_notes", parsed.get("status", "unknown"), dur)
        if parsed.get("status") != "success":
            raise RuntimeError(f"MCP Tool error: {parsed.get('message')}")
        return parsed.get("data", [])

    def search_notes(self, course_id: int, query: str = "", unit: str = "") -> List[Dict[str, Any]]:
        """Invokes MCP Tool: search_course_notes."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = search_course_notes(course_id=course_id, query=query, unit=unit)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "search_course_notes", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {}).get("notes", [])

    def get_note_by_id(self, note_id: int) -> Dict[str, Any]:
        """Invokes MCP Tool: get_note."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = get_note(note_id=note_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "get_note", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {})

    # ── Read 'assignment & rubric definitions' ────────────────────────────────

    def read_assignment_rubric(self, assignment_id: int) -> Dict[str, Any]:
        """Invokes MCP Tool: fetch_assignment_rubric."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = fetch_assignment_rubric(assignment_id=assignment_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "fetch_assignment_rubric", parsed.get("status", "unknown"), dur)
        if parsed.get("status") != "success":
            raise RuntimeError(f"MCP Tool error: {parsed.get('message')}")
        return parsed.get("data", {})

    def list_course_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Invokes MCP Tool: get_assignments."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = get_assignments(course_id=course_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "get_assignments", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {}).get("assignments", [])

    def validate_rubric(self, title: str, max_marks: float, rubric: Any) -> Dict[str, Any]:
        """Invokes MCP Tool: validate_assignment."""
        self._verify_auth()
        t0 = time.perf_counter()
        rubric_str = json.dumps(rubric) if not isinstance(rubric, str) else rubric
        raw_json = validate_assignment(title=title, max_marks=max_marks, rubric_json=rubric_str)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "validate_assignment", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {})

    # ── Read 'submission records' ─────────────────────────────────────────────

    def read_submission_records(self, assignment_id: int) -> List[Dict[str, Any]]:
        """Invokes MCP Tool: fetch_submissions."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = fetch_submissions(assignment_id=assignment_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "fetch_submissions", parsed.get("status", "unknown"), dur)
        if parsed.get("status") != "success":
            raise RuntimeError(f"MCP Tool error: {parsed.get('message')}")
        return parsed.get("data", [])

    def get_single_submission(self, submission_id: int) -> Dict[str, Any]:
        """Invokes MCP Tool: get_submission."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = get_submission(submission_id=submission_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "get_submission", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {})

    # ── Read 'project milestones' ─────────────────────────────────────────────

    def read_milestones(self, course_id: int) -> List[Dict[str, Any]]:
        """Invokes MCP Tool: fetch_project_milestones."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = fetch_project_milestones(course_id=course_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "fetch_project_milestones", parsed.get("status", "unknown"), dur)
        return parsed.get("data", [])

    def list_project_groups(self, course_id: int) -> List[Dict[str, Any]]:
        """Invokes MCP Tool: get_project_groups."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = get_project_groups(course_id=course_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "get_project_groups", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {}).get("groups", [])

    # ── Approvals and Governance ──────────────────────────────────────────────

    def list_pending_approvals(self, course_id: int = 0) -> List[Dict[str, Any]]:
        """Invokes MCP Tool: get_pending_approvals."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = get_pending_approvals(course_id=course_id)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "get_pending_approvals", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {}).get("grades", [])

    def submit_faculty_approval(self, grade_id: int, faculty_id: int, final_marks: Optional[float] = None) -> Dict[str, Any]:
        """Invokes MCP Tool: approve_grade."""
        self._verify_auth()
        t0 = time.perf_counter()
        raw_json = approve_grade(grade_id=grade_id, faculty_id=faculty_id, final_marks=final_marks)
        dur = (time.perf_counter() - t0) * 1000
        parsed = json.loads(raw_json)
        self._log_mcp_access("mcp_tool_call", "approve_grade", parsed.get("status", "unknown"), dur)
        return parsed.get("data", {})

    # ── Read URI-based MCP Resources ─────────────────────────────────────────

    def read_resource_uri(self, uri: str) -> Dict[str, Any]:
        """Reads MCP resources via standard URI protocol (notes://, assignments://, submissions://, milestones://)."""
        self._verify_auth()
        t0 = time.perf_counter()
        if uri.startswith("notes://"):
            course_id = int(uri.replace("notes://", ""))
            res = json.loads(get_notes_resource(course_id))
        elif uri.startswith("assignments://"):
            course_id = int(uri.replace("assignments://", ""))
            res = json.loads(get_assignments_resource(course_id))
        elif uri.startswith("submissions://"):
            assignment_id = int(uri.replace("submissions://", ""))
            res = json.loads(get_submissions_resource(assignment_id))
        elif uri.startswith("milestones://"):
            course_id = int(uri.replace("milestones://", ""))
            res = json.loads(get_milestones_resource(course_id))
        else:
            raise ValueError(f"Unsupported MCP resource URI scheme: {uri}")

        dur = (time.perf_counter() - t0) * 1000
        self._log_mcp_access("mcp_resource_read", uri, "success", dur)
        return res
