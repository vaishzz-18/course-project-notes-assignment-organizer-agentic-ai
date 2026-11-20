"""
Acceptance Test Suite for Lab 5: MCP-Style Connector — One Server for All Sources
Verifies:
1. Real FastMCP server tools: fetch_notes, fetch_assignment_rubric, fetch_submissions, fetch_project_milestones.
2. Real FastMCP resource URIs: notes://, assignments://, submissions://.
3. Governed connector client decouples all agent data access from underlying storage.
4. Pseudocode contract verification:
   connector.expose:
     read('the notes/materials store')
     read('assignment & rubric definitions')
     read('submission records')
   agents.use(connector)
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from connector.mcp_connector_client import GovernedMCPConnectorClient


def test_lab5_read_notes_via_mcp_connector():
    """Acceptance Test 1: Reads notes store through MCP tool interface."""
    connector = GovernedMCPConnectorClient()
    notes = connector.read_notes_store(course_id=1)
    
    assert len(notes) >= 3
    assert any(n["unit"] == "Unit 1" for n in notes)
    assert any(n["version"] == 2 for n in notes)
    print(f"\n[PASS] MCP Tool fetch_notes: {len(notes)} materials retrieved through MCP protocol.")


def test_lab5_read_rubric_via_mcp_connector():
    """Acceptance Test 2: Reads assignment rubric through MCP tool interface."""
    connector = GovernedMCPConnectorClient()
    assignment = connector.read_assignment_rubric(assignment_id=1)

    assert assignment["id"] == 1
    assert assignment["max_marks"] == 100.0
    assert "code_correctness" in assignment["rubric"]
    print(f"\n[PASS] MCP Tool fetch_assignment_rubric: '{assignment['title']}' loaded through MCP.")


def test_lab5_read_submissions_via_mcp_connector():
    """Acceptance Test 3: Reads submission records through MCP tool interface."""
    connector = GovernedMCPConnectorClient()
    submissions = connector.read_submission_records(assignment_id=1)

    assert len(submissions) >= 5
    # Verify late flag and similarity flags are transmitted over MCP
    late_cases = [s for s in submissions if s["is_late"]]
    assert len(late_cases) >= 1
    high_sim = [s for s in submissions if (s["similarity_score"] or 0) > 0.75]
    assert len(high_sim) >= 1
    print(f"\n[PASS] MCP Tool fetch_submissions: {len(submissions)} records (Late: {len(late_cases)}, Plagiarism flagged: {len(high_sim)}).")


def test_lab5_mcp_resource_uris():
    """Acceptance Test 4: Verifies standard MCP Resource URI schemas."""
    connector = GovernedMCPConnectorClient()

    notes_res = connector.read_resource_uri("notes://1")
    assert notes_res["course_id"] == 1
    assert len(notes_res["notes"]) >= 3

    assign_res = connector.read_resource_uri("assignments://1")
    assert assign_res["course_id"] == 1
    assert len(assign_res["assignments"]) >= 1

    subs_res = connector.read_resource_uri("submissions://1")
    assert subs_res["assignment_id"] == 1
    assert len(subs_res["submissions"]) >= 5
    print("\n[PASS] MCP Resource URIs (notes://, assignments://, submissions://) verified.")


def test_lab5_pseudocode_contract():
    """
    Acceptance Test 5: Verifies pseudocode:
    connector.expose:
      read('the notes/materials store')
      read('assignment & rubric definitions')
      read('submission records')
    agents.use(connector)
    """
    connector = GovernedMCPConnectorClient()
    
    # Simulate agent consuming exclusively from connector
    store_notes = connector.read_notes_store(course_id=1)
    definitions = connector.read_assignment_rubric(assignment_id=1)
    records = connector.read_submission_records(assignment_id=1)

    assert len(store_notes) > 0
    assert definitions["max_marks"] == 100.0
    assert len(records) > 0
    assert len(connector.audit_log) >= 3
    assert all(entry["governed_by"] == "GovernedMCPConnectorClient" for entry in connector.audit_log)
    print("\n[PASS] Lab 5 Pseudocode Contract verified: No agent directly touches DB; all use connector.")


if __name__ == "__main__":
    test_lab5_read_notes_via_mcp_connector()
    test_lab5_read_rubric_via_mcp_connector()
    test_lab5_read_submissions_via_mcp_connector()
    test_lab5_mcp_resource_uris()
    test_lab5_pseudocode_contract()
    print("\nALL LAB 5 ACCEPTANCE TESTS PASSED!")
