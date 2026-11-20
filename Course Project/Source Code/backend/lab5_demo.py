"""
Interactive Demonstration CLI for Lab 5: MCP-Style Connector (One Server for All Sources)
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Real Model Context Protocol (FastMCP) server tools & resource URIs
2. GovernedMCPConnectorClient acting as the sole data access gateway
3. Zero direct database queries by specialist agents
4. Full MCP protocol audit log
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from connector.mcp_connector_client import GovernedMCPConnectorClient


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab5_demonstration():
    connector = GovernedMCPConnectorClient()

    print_banner("LAB 5: MCP-STYLE CONNECTOR (ONE SERVER FOR ALL SOURCES)")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Protocol: Anthropic Model Context Protocol (FastMCP)")
    print("Governing Rule: No agent touches a source directly; all access goes through MCP.\n")

    # -------------------------------------------------------------
    # 1. MCP Tools Execution
    # -------------------------------------------------------------
    print_banner("1. CALLING MCP TOOLS VIA GOVERNED CONNECTOR")
    
    print("Agent requests Notes -> calls connector.read_notes_store(course_id=1)...")
    notes = connector.read_notes_store(course_id=1)
    print(f"  MCP Response: Received {len(notes)} note items.")
    for n in notes:
        tag = "[CURRENT]" if n.get("is_current") else "[ARCHIVED]"
        print(f"    * {tag} {n['unit']} | {n['title']} (v{n['version']})")

    print("\nAgent requests Assignment 1 -> calls connector.read_assignment_rubric(1)...")
    assignment = connector.read_assignment_rubric(assignment_id=1)
    print(f"  MCP Response: Loaded '{assignment['title']}' (Max Marks: {assignment['max_marks']})")
    print(f"  Rubric Criteria: {list(assignment['rubric'].keys())}")

    print("\nAgent requests Submissions -> calls connector.read_submission_records(1)...")
    submissions = connector.read_submission_records(assignment_id=1)
    print(f"  MCP Response: Received {len(submissions)} submission records:")
    for s in submissions:
        late_badge = "LATE" if s["is_late"] else "ON-TIME"
        sim_badge = f"SIMILARITY={s['similarity_score']:.0%}"
        if (s["similarity_score"] or 0) > 0.75:
            sim_badge += " [PLAGIARISM FLAG]"
        print(f"    * Student: {s['student_name']} | {late_badge} | {sim_badge}")

    print("\nAgent requests Milestones -> calls connector.read_milestones(course_id=1)...")
    milestones = connector.read_milestones(course_id=1)
    print(f"  MCP Response: Received {len(milestones)} milestone records:")
    for m in milestones:
        health_str = (m.get('health') or 'NOT_STARTED').upper()
        grp_str = m.get('group_name') or 'All Groups'
        print(f"    * Checkpoint {m['checkpoint_number']}: {m['title']} | Group: {grp_str} | Health: {health_str}")

    # -------------------------------------------------------------
    # 2. MCP URI Resources
    # -------------------------------------------------------------
    print_banner("2. READING MCP URI-ADDRESSABLE RESOURCES")
    print("Reading notes://1 ...")
    res_notes = connector.read_resource_uri("notes://1")
    print(f"  Resource URI content: {len(res_notes['notes'])} notes items.")

    print("Reading assignments://1 ...")
    res_assign = connector.read_resource_uri("assignments://1")
    print(f"  Resource URI content: {len(res_assign['assignments'])} assignments items.")

    print("Reading submissions://1 ...")
    res_subs = connector.read_resource_uri("submissions://1")
    print(f"  Resource URI content: {len(res_subs['submissions'])} submissions items.")

    # -------------------------------------------------------------
    # 3. Governance Audit Trail
    # -------------------------------------------------------------
    print_banner("3. CONNECTOR GOVERNANCE & PROTOCOL AUDIT TRAIL")
    print(f"Total governed operations logged: {len(connector.audit_log)}")
    for log in connector.audit_log:
        print(f"  [MCP AUDIT] Action: {log['action']} -> Target: {log['target']} (Status: {log['status']})")

    print_banner("LAB 5 DEMONSTRATION COMPLETE: ALL DATA EXCLUSIVELY ACCESSED VIA MCP")


if __name__ == "__main__":
    run_lab5_demonstration()
