"""
Acceptance Test Suite for Lab 2: Tool-Using Agent — Call Data & Compute
Verifies:
1. Notes repository read via typed tool (verifies versioning).
2. Assignment & rubric read via typed tool.
3. Deadline compliance computed mathematically (flags late submissions with exact delta).
4. Rubric calculation computes exact score and validates 0 <= marks <= max_marks.
5. Boundary violation rejected (marks > max_marks returns valid=False).
6. Similarity threshold verification (flags high matches for human review).
7. Full pseudocode assertion:
   a = tool.read(...)
   b = tool.read(...)
   v = tool.compute(...)
   assert v.valid
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.course_tools import (
    tool_read_notes_store,
    tool_read_assignment_rubric,
    tool_compute_deadline_compliance,
    tool_compute_rubric_total,
    tool_verify_similarity
)
from agents.tool_using_agent import CourseToolAgent


def test_lab2_read_notes_store_tool():
    """Acceptance Test 1: Reads notes store through typed tool, verifying versioned materials."""
    agent = CourseToolAgent()
    res = agent.read_notes(course_id=1)
    
    assert res.valid
    assert res.count >= 3
    # Check that Unit 1 has version 2 marked current
    u1_notes = [n for n in res.notes if n.unit == "Unit 1"]
    assert len(u1_notes) >= 1
    current_u1 = [n for n in u1_notes if n.is_current][0]
    assert current_u1.version == 2
    print(f"\n[PASS] Notes store read via tool: {res.count} notes found, Unit 1 current version = {current_u1.version}.")


def test_lab2_read_assignment_rubric_tool():
    """Acceptance Test 2: Reads assignment definition and parses rubric criteria through typed tool."""
    agent = CourseToolAgent()
    res = agent.read_assignment_rubric(assignment_id=1)

    assert res.valid
    assert res.max_marks == 100.0
    assert len(res.criteria) == 4
    rubric_sum = sum(c.max_marks for c in res.criteria)
    assert rubric_sum == 100.0
    print(f"\n[PASS] Rubric read via tool: '{res.title}', Max Marks = {res.max_marks}, Criteria count = {len(res.criteria)}.")


def test_lab2_compute_deadline_compliance_tool():
    """Acceptance Test 3: Computes deadline timing mathematically without LLM hallucination."""
    agent = CourseToolAgent()
    due_date = "2026-10-10T12:00:00"

    # Case A: On time submission
    on_time_sub = "2026-10-09T10:00:00"
    res_on_time = agent.compute_submission_compliance(on_time_sub, due_date)
    assert not res_on_time.is_late
    assert "On Time" in res_on_time.delta_formatted

    # Case B: Late submission (Marcus Vance case)
    late_sub = "2026-10-12T14:30:00"
    res_late = agent.compute_submission_compliance(late_sub, due_date)
    assert res_late.is_late
    assert res_late.penalty_recommended
    assert "2d 2h 30m LATE" in res_late.delta_formatted
    print(f"\n[PASS] Deadline compliance computed via tool:")
    print(f"  On-time case: {res_on_time.delta_formatted}")
    print(f"  Late case: {res_late.delta_formatted}")


def test_lab2_compute_rubric_total_valid_and_boundary_violation():
    """Acceptance Test 4 & 5: Validates rubric summation and rejects out-of-bounds calculations."""
    agent = CourseToolAgent()
    rubric_max = 100.0

    # Valid score breakdown
    scores_valid = {
        "code_correctness": 38.0,
        "react_loop_reasoning": 24.0,
        "error_handling": 18.0,
        "documentation": 14.0
    }
    calc_valid = agent.compute_rubric_score(scores_valid, rubric_max)
    assert calc_valid.valid
    assert calc_valid.total_awarded == 94.0
    assert calc_valid.percentage == 94.0
    assert calc_valid.is_within_bounds

    # Boundary violation: Score exceeds rubric maximum!
    scores_overflow = {
        "code_correctness": 45.0,  # Max was 40
        "react_loop_reasoning": 30.0,
        "error_handling": 25.0,
        "documentation": 20.0
    }
    calc_invalid = agent.compute_rubric_score(scores_overflow, rubric_max)
    assert not calc_invalid.valid, "Sum exceeds max marks; must fail validation!"
    assert not calc_invalid.is_within_bounds
    assert "Math Error" in calc_invalid.discrepancy_note
    print(f"\n[PASS] Rubric math verified via tool:")
    print(f"  Valid sum: {calc_valid.total_awarded} / {calc_valid.rubric_max} ({calc_valid.percentage}%)")
    print(f"  Caught Boundary Overflow: Total {calc_invalid.total_awarded} > {calc_invalid.rubric_max} -> Flagged: {calc_invalid.discrepancy_note}")


def test_lab2_similarity_threshold_verification():
    """Acceptance Test 6: Verifies similarity scores and flags potential plagiarism for faculty review."""
    agent = CourseToolAgent()

    # Normal submission
    sim_normal = agent.verify_similarity(0.12)
    assert not sim_normal.is_flagged_for_review
    assert sim_normal.severity == "LOW"

    # High similarity submission (David Kim copying Alex Chen, 96%)
    sim_critical = agent.verify_similarity(0.96)
    assert sim_critical.is_flagged_for_review
    assert sim_critical.severity == "CRITICAL"
    assert "Immediate faculty review required" in sim_critical.recommendation
    print(f"\n[PASS] Similarity checked via tool: Score 0.96 -> Flagged: {sim_critical.severity}, {sim_critical.recommendation}")


def test_lab2_pseudocode_end_to_end_contract():
    """
    Acceptance Test 7: Verifies exact pseudocode contract:
    a = tool.read('the notes/materials store')
    b = tool.read('assignment & rubric definitions')
    v = tool.compute(a, b)
    assert v.valid
    """
    agent = CourseToolAgent()
    notes = agent.read_notes(course_id=1)
    assignment = agent.read_assignment_rubric(assignment_id=1)
    
    # Compute grade from actual rubric
    criteria_scores = {c.criterion: c.max_marks * 0.9 for c in assignment.criteria}
    v = agent.compute_rubric_score(criteria_scores, assignment.max_marks)

    assert notes.valid
    assert assignment.valid
    assert v.valid
    print(f"\n[PASS] Lab 2 Pseudocode Assertion verified: a={notes.count} notes, b='{assignment.title}', v={v.total_awarded}/{v.rubric_max} (valid={v.valid}).")


if __name__ == "__main__":
    test_lab2_read_notes_store_tool()
    test_lab2_read_assignment_rubric_tool()
    test_lab2_compute_deadline_compliance_tool()
    test_lab2_compute_rubric_total_valid_and_boundary_violation()
    test_lab2_similarity_threshold_verification()
    test_lab2_pseudocode_end_to_end_contract()
    print("\nALL LAB 2 ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
