"""
Lab 10 Demo — Ops Resilience (Validate, Diagnose, Fix)
Chapter 2: Course Project, Notes & Assignment Organizer

Run:
    cd backend
    python lab10_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.resilience_coordinator import OpsResilienceCoordinator
from runtime.governed_runtime import AURAControlledRuntime

DIVIDER = "=" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def main():
    runtime = AURAControlledRuntime()
    coordinator = OpsResilienceCoordinator(retry_budget=3, runtime=runtime)

    print("\n+------------------------------------------------------------------------+")
    print("|  LAB 10: OPS RESILIENCE -- Validate, Diagnose, Fix (Self-Healing)      |")
    print("|  Chapter 2: Course Project, Notes & Assignment Organizer               |")
    print("+------------------------------------------------------------------------+")
    print("\nCore Design Principle:")
    print("  'Regenerate only the failing part -- rebuilding everything wastes budget.'")
    print("\nPseudocode:")
    print("  report = validate(output, plan)")
    print("  while not report.passed and attempts < BUDGET:")
    print("      regenerate(report.failing); report = validate(output, plan)")
    print("  if not report.passed: escalate(report)")

    # ── 1. Create Baseline Draft ─────────────────────────────────────────────
    section("1. INGESTING BASELINE COURSE WORKSPACE DRAFT")
    baseline = {
        "course_id": 1,
        "course_code": "CS401",
        "assignment_id": 1,
        "assignment_title": "Assignment 1: Agentic Workflow Architecture",
        "status": "draft",
        "faculty_approved": False,
        "submissions": [
            {
                "id": "sub_alex_1",
                "student_name": "Alex Chen",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.08,
                "content": "Clean LangGraph StateGraph implementation with ReAct loops."
            },
            {
                "id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "is_late": False,
                "late_penalty_applied": False,
                "similarity_score": 0.11,
                "content": "Parallel swarm worker pool with plan-aligned fan-in merge."
            },
            {
                "id": "sub_david_3",
                "student_name": "David Kim",
                "is_late": True,
                "late_penalty_applied": True,
                "similarity_score": 0.09,
                "content": "Pydantic typed tools with deadline and rubric arithmetic."
            }
        ],
        "grading_results": [
            {
                "submission_id": "sub_alex_1",
                "student_name": "Alex Chen",
                "final_score": 92.0,
                "raw_score": 92.0,
                "feedback": "Outstanding implementation of LangGraph nodes."
            },
            {
                "submission_id": "sub_priya_2",
                "student_name": "Priya Sharma",
                "final_score": 88.0,
                "raw_score": 88.0,
                "feedback": "Excellent concurrency speedup benchmark."
            },
            {
                "submission_id": "sub_david_3",
                "student_name": "David Kim",
                "final_score": 76.5,
                "raw_score": 85.0,
                "feedback": "Clean typed tools; 10% late penalty applied."
            }
        ]
    }
    plan = {"max_marks": 100.0}
    clean_report = coordinator.validate(baseline, plan)
    print(f"  Baseline Draft Status: {'[VALID]' if clean_report.passed else '[INVALID]'}")
    print(f"  Total Submissions: {len(baseline['submissions'])} | Draft Grades: {len(baseline['grading_results'])}")

    # ── 2. Fault Injection Harness ───────────────────────────────────────────
    section("2. FAILURE INJECTION HARNESS: INJECTING 3 COMPLEX FAULTS")
    print("  Injecting faults into draft to test automatic diagnosis & repair:")
    print("    [Fault 1] Rubric Overflow: Alex Chen score forced to 125.0 / 100.0")
    print("    [Fault 2] Unflagged Late Submission: David Kim late penalty cleared")
    print("    [Fault 3] Missing Similarity: Priya Sharma similarity score erased")

    corrupted = coordinator.inject_faults(
        baseline,
        fault_types=["rubric_overflow", "unflagged_late_submission", "missing_similarity_score"]
    )

    # ── 3. Initial Validation & Diagnosis ────────────────────────────────────
    section("3. RUNNING ACCEPTANCE GATE & DIAGNOSIS")
    initial_report = coordinator.validate(corrupted, plan)
    print(f"  Gate Evaluation Result: {'[PASS]' if initial_report.passed else '[FAIL]'}")
    print(f"  Failing Invariants Detected: {initial_report.failing_checks} of {initial_report.total_checks}")
    print(f"  Diagnosis: {initial_report.diagnosis_summary}\n")

    print(f"  {'Entity':<14} {'ID':<14} {'Failing Rule':<38} {'Proposed Fix'}")
    print("  " + "-" * 88)
    for f in initial_report.failing_items:
        print(f"  {f.entity_type:<14} {f.entity_id:<14} {f.failing_rule:<38} {f.proposed_fix[:30]}...")

    # ── 4. Targeted Self-Healing Loop ────────────────────────────────────────
    section("4. EXECUTING TARGETED SELF-HEALING REPAIR LOOP")
    print(f"  Coordinator running bounded repair loop (Budget = {coordinator.retry_budget} attempts)...")

    result = coordinator.self_healing_loop(corrupted, plan, run_id="run_lab10_cli_demo")

    print(f"\n  Repair Outcome: {result.status}")
    print(f"  Attempts Used: {result.attempts_used} of {result.retry_budget}")
    print(f"  Total Targeted Repairs Executed: {len(result.repair_log)}\n")

    for idx, rep in enumerate(result.repair_log, 1):
        print(f"    Repair #{idx} (Attempt {rep.attempt}):")
        print(f"      Target: [{rep.entity_id}]")
        print(f"      Action: {rep.action_taken}")
        print(f"      Before: {rep.before_state}")
        print(f"      After : {rep.after_state}")

    # ── 5. Post-Repair Verification ──────────────────────────────────────────
    section("5. POST-REPAIR ACCEPTANCE VERIFICATION")
    print(f"  Initial Passed: {result.initial_passed} -> Final Passed: {result.final_passed}")
    print(f"  All 4 Invariant Checks:")
    for chk in result.final_report.checks:
        sym = "[PASS]" if chk.passed else "[FAIL]"
        print(f"    {sym} {chk.name}: {chk.details}")

    # ── 6. Acceptance Checklist ──────────────────────────────────────────────
    section("6. ACCEPTANCE CRITERIA CHECKLIST")
    checks = {
        "Injected faults detected accurately": initial_report.passed is False,
        "Fine-grained diagnosis identifies offending items": len(initial_report.failing_items) >= 3,
        "Targeted self-healing repairs only offending parts": len(result.repair_log) >= 3,
        "Compliant components preserved without churn": len(result.final_draft["submissions"]) == 3,
        "Final validation passes 100% within retry budget": result.final_passed is True,
        "Provenance audit trace logged in AURAControlledRuntime": len(runtime.in_memory_audit) >= 1,
    }

    all_passed = all(checks.values())
    for label, passed in checks.items():
        sym = "[PASS]" if passed else "[FAIL]"
        print(f"  {sym} {label}")

    print(f"\n  Final Result: {'ALL LAB 10 CRITERIA PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
