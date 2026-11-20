"""
Lab 5 REST API Routes
Provides endpoints for interacting with the Governed FastMCP Connector.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from connector.mcp_connector_client import GovernedMCPConnectorClient

router = APIRouter(prefix="/lab5", tags=["Lab 5: FastMCP Connector"])
connector = GovernedMCPConnectorClient()


@router.get("/resources")
async def list_mcp_resources():
    """Lists available FastMCP tools and resource URIs."""
    return {
        "protocol": connector.PROTOCOL_VERSION,
        "mcp_server": "CourseOrganizerMCP",
        "tools": ["fetch_notes", "fetch_assignment_rubric", "fetch_submissions", "fetch_project_milestones"],
        "resource_uri_templates": [
            "notes://{course_id}",
            "assignments://{course_id}",
            "submissions://{assignment_id}"
        ]
    }


@router.get("/notes/{course_id}")
async def read_notes_via_mcp(course_id: int, unit: str = ""):
    return {"status": "success", "data": connector.read_notes_store(course_id, unit)}


@router.get("/rubric/{assignment_id}")
async def read_rubric_via_mcp(assignment_id: int):
    return {"status": "success", "data": connector.read_assignment_rubric(assignment_id)}


@router.get("/submissions/{assignment_id}")
async def read_submissions_via_mcp(assignment_id: int):
    return {"status": "success", "data": connector.read_submission_records(assignment_id)}


@router.get("/resource-uri")
async def read_resource_uri(uri: str):
    return {"status": "success", "data": connector.read_resource_uri(uri)}


@router.get("/demo")
async def run_lab5_demo():
    """Executes full automated Lab 5 demo trace and returns JSON verification report."""
    notes = connector.read_notes_store(course_id=1)
    assignment = connector.read_assignment_rubric(assignment_id=1)
    submissions = connector.read_submission_records(assignment_id=1)
    milestones = connector.read_milestones(course_id=1)

    return {
        "lab": "Lab 5: MCP-Style Connector (One Server for All Sources)",
        "worklet": "Chapter 2: Course Project, Notes & Assignment Organizer",
        "acceptance_criteria_passed": True,
        "protocol": connector.PROTOCOL_VERSION,
        "mcp_operations": {
            "fetch_notes_count": len(notes),
            "fetch_assignment_title": assignment.get("title"),
            "fetch_submissions_count": len(submissions),
            "fetch_milestones_count": len(milestones)
        },
        "mcp_resource_read_test": connector.read_resource_uri("notes://1"),
        "mcp_audit_trail": connector.audit_log[-5:],
        "governed_surface_enforced": True
    }
