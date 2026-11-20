"""
Interactive Demonstration CLI for Lab 2: Tool-Using Agent (Call Data & Compute)
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Contrast with Naive Chatbot (Hallucinating dates, guessing rubric totals)
2. Tool-Using Agent Execution Trace:
   - Reader: Notes/materials store with versioning
   - Reader: Assignment definition & rubric criteria
   - Compute: Deadline compliance (on-time vs late calculation)
   - Compute: Rubric arithmetic & boundary invariant check
   - Compute: Similarity / Plagiarism threshold checker
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from agents.tool_using_agent import CourseToolAgent


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab2_demonstration():
    agent = CourseToolAgent()

    print_banner("LAB 2: TOOL-USING AGENT (CALL DATA & COMPUTE)")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Design Principle: Never assert a fact in the prompt that a tool should verify.\n")

    # -------------------------------------------------------------
    # Scenario 1: Contrast with Hallucinating Chatbot
    # -------------------------------------------------------------
    print_banner("SCENARIO 1: The Naive Chatbot (Why Hallucinated Math Fails)")
    print("Query: 'Is Marcus Vance's submission late, and what is his score if he got 35, 22, 18, 15?'")
    print("\nNaive Chatbot says:")
    print("  'I think his submission was probably on time. And the total marks are roughly 95.'")
    print("  --> Failure: Hallucinated the date delta, did inaccurate mental arithmetic, checked zero rubrics.")

    # -------------------------------------------------------------
    # Scenario 2: Tool-Using Agent (Reading Data Store)
    # -------------------------------------------------------------
    print_banner("SCENARIO 2: Reading Notes Repository via Typed Tool")
    print("Invoking Tool: tool_read_notes_store(course_id=1)")
    notes_res = agent.read_notes(course_id=1)
    print(f"\n[Tool Output: ReadNotesOutput (valid={notes_res.valid})]")
    print(f"  Total Notes Found: {notes_res.count}")
    for n in notes_res.notes:
        tag = "[CURRENT]" if n.is_current else "[SUPERSEDED]"
        print(f"    - {tag} {n.unit} | {n.title} (v{n.version}) -> {n.file_name}")

    # -------------------------------------------------------------
    # Scenario 3: Reading Rubric Definitions
    # -------------------------------------------------------------
    print_banner("SCENARIO 3: Reading Assignment Rubric via Typed Tool")
    print("Invoking Tool: tool_read_assignment_rubric(assignment_id=1)")
    rubric_res = agent.read_assignment_rubric(assignment_id=1)
    print(f"\n[Tool Output: ReadRubricOutput (valid={rubric_res.valid})]")
    print(f"  Assignment: {rubric_res.title}")
    print(f"  Max Marks: {rubric_res.max_marks}")
    print(f"  Due Date: {rubric_res.due_date}")
    print("  Rubric Breakdown:")
    for c in rubric_res.criteria:
        print(f"    * {c.criterion}: {c.max_marks} marks ({c.description})")

    # -------------------------------------------------------------
    # Scenario 4: Computing Deadline Compliance
    # -------------------------------------------------------------
    print_banner("SCENARIO 4: Computing Deadline Compliance Strictly via Compute Tool")
    print("Case A: Marcus Vance Submission (Submitted: 2026-10-15 vs Due: 2026-10-07)")
    timing_res = agent.compute_submission_compliance(
        submitted_at="2026-10-15T14:30:00",
        due_date=rubric_res.due_date
    )
    print(f"\n[Tool Output: DeadlineComplianceOutput (valid={timing_res.valid})]")
    print(f"  Is Late: {timing_res.is_late}")
    print(f"  Exact Timing Delta: {timing_res.delta_formatted}")
    print(f"  Penalty Recommended: {timing_res.penalty_recommended}")

    # -------------------------------------------------------------
    # Scenario 5: Computing Rubric Math & Boundary Validation
    # -------------------------------------------------------------
    print_banner("SCENARIO 5: Computing Rubric Math & Invariant Check (0 <= score <= max)")
    awarded_scores = {
        "code_correctness": 38.0,
        "react_loop_reasoning": 23.5,
        "error_handling": 19.0,
        "documentation": 14.0
    }
    print(f"Criteria marks awarded: {awarded_scores}")
    calc_res = agent.compute_rubric_score(awarded_scores, rubric_res.max_marks)
    print(f"\n[Tool Output: RubricComputeOutput (valid={calc_res.valid})]")
    print(f"  Total Awarded: {calc_res.total_awarded} / {calc_res.rubric_max}")
    print(f"  Calculated Percentage: {calc_res.percentage}%")
    print(f"  Is Within Boundary: {calc_res.is_within_bounds}")

    # -------------------------------------------------------------
    # Scenario 6: Boundary Protection (Rejecting Hallucinated Math)
    # -------------------------------------------------------------
    print_banner("SCENARIO 6: Invariant Enforcement (Rejecting Invalid Grade Draft)")
    overflow_scores = {
        "code_correctness": 50.0,
        "react_loop_reasoning": 35.0,
        "error_handling": 25.0,
        "documentation": 20.0
    }
    print(f"Attempting to award: {overflow_scores} (Sum = {sum(overflow_scores.values())} > {rubric_res.max_marks})")
    overflow_res = agent.compute_rubric_score(overflow_scores, rubric_res.max_marks)
    print(f"\n[Tool Output: RubricComputeOutput (valid={overflow_res.valid})]")
    print(f"  Flagged Error: {overflow_res.discrepancy_note}")
    print("  --> Invariant Protected: Coordinator rejects any grade draft that exceeds rubric maximum!")

    # -------------------------------------------------------------
    # Scenario 7: Similarity Verification Tool
    # -------------------------------------------------------------
    print_banner("SCENARIO 7: Plagiarism / Similarity Threshold Tool")
    print("David Kim submission similarity score: 0.96 (Threshold: 0.75)")
    sim_res = agent.verify_similarity(0.96)
    print(f"\n[Tool Output: SimilarityCheckOutput (valid={sim_res.valid})]")
    print(f"  Flagged for Faculty Review: {sim_res.is_flagged_for_review}")
    print(f"  Severity: {sim_res.severity}")
    print(f"  Action: {sim_res.recommendation}")

    # -------------------------------------------------------------
    # Scenario 8: Pseudocode Invariant Assertion
    # -------------------------------------------------------------
    print_banner("SCENARIO 8: Pseudocode Invariant Assertion")
    print("Testing Lab 2 Pseudocode:")
    print("  a = tool.read('the notes/materials store')")
    print("  b = tool.read('assignment & rubric definitions')")
    print("  v = tool.compute(a, b)")
    print("  assert v.valid")

    a = agent.read_notes(course_id=1)
    b = agent.read_assignment_rubric(assignment_id=1)
    v = agent.compute_rubric_score({c.criterion: c.max_marks for c in b.criteria}, b.max_marks)
    assert v.valid
    print(f"  Result: a={a.count} notes, b='{b.title}', v={v.total_awarded}/{v.rubric_max} -> assert v.valid PASSED!")

    print_banner("LAB 2 DEMONSTRATION COMPLETE: ALL DATA & COMPUTE GOVERNED BY TOOLS")


if __name__ == "__main__":
    run_lab2_demonstration()
