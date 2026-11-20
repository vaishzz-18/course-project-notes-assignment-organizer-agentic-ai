"""
Lab 11 Demo — SDLC Factory (Spec → Tested Output)
Chapter 2: Course Project, Notes & Assignment Organizer

Run:
    cd backend
    python lab11_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.sdlc_factory import SDLCWorkspaceFactory
from runtime.governed_runtime import AURAControlledRuntime

DIVIDER = "=" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def main():
    runtime = AURAControlledRuntime()
    factory = SDLCWorkspaceFactory(runtime=runtime)

    print("\n+------------------------------------------------------------------------+")
    print("|  LAB 11: SDLC FACTORY -- Spec -> Tested Output & Acceptance Gate       |")
    print("|  Chapter 2: Course Project, Notes & Assignment Organizer               |")
    print("+------------------------------------------------------------------------+")
    print("\nCore Design Principle:")
    print("  'The acceptance suite is the gate; never let a result skip to the human without a green report.'")
    print("\nPseudocode:")
    print("  artifact = build(plan)")
    print("  report   = acceptance_suite(artifact, plan)")
    print("  require report.all_pass   # gate before human review")

    # ── 1. Plan Specification ────────────────────────────────────────────────
    section("1. LOCKED COURSE PLAN SPECIFICATION (INPUT SPEC)")
    plan_spec = {
        "course_code": "CS401",
        "course_name": "Agentic AI & Autonomous Systems",
        "faculty": "Dr. Vaishnavi Patel",
        "max_marks": 100.0,
        "units": [
            {"unit": "Unit 1", "title": "ReAct Cognitive Loops & Planner Engines"},
            {"unit": "Unit 2", "title": "Tool-Using Agents & Zero-Hallucination Math"},
            {"unit": "Unit 3", "title": "LangGraph StateGraphs & Back-Edges"},
            {"unit": "Unit 4", "title": "Parallel Multi-Agent Swarms"}
        ],
        "assignments": [
            {
                "id": 1,
                "title": "Assignment 1: Agentic Workflow Architecture",
                "max_marks": 100.0,
                "due_date": "2026-10-15T23:59:59Z"
            }
        ],
        "milestones": [
            {"checkpoint": 1, "title": "Core Agentic Architecture", "week": 4},
            {"checkpoint": 2, "title": "Swarm Benchmarking", "week": 8}
        ]
    }

    print(f"  Course Code : {plan_spec['course_code']} - {plan_spec['course_name']}")
    print(f"  Faculty     : {plan_spec['faculty']}")
    print(f"  Max Marks   : {plan_spec['max_marks']}")
    print(f"  Total Units : {len(plan_spec['units'])}")
    print(f"  Assignments : {len(plan_spec['assignments'])} | Milestones: {len(plan_spec['milestones'])}")

    # ── 2. Factory Build Command ─────────────────────────────────────────────
    section("2. EXECUTING FACTORY BUILD: artifact = build(plan)")
    print("  Assembling full workspace pipeline:")
    print("    [Step 1] Ingesting locked specification constraints...")
    print("    [Step 2] Executing parallel swarm on student submissions...")
    print("    [Step 3] Running deep research evidence grounding on claims...")
    print("    [Step 4] Running ops resilience self-healing on boundary invariants...")

    artifact = factory.build(plan=plan_spec, course_id=1, faculty_id=1, run_self_healing=True)

    print(f"\n  Build Complete!")
    print(f"    Build ID       : {artifact.build_id}")
    print(f"    Build Latency  : {artifact.build_time_ms:.1f} ms")
    print(f"    Artifact Status: {artifact.workspace['status']}")
    print(f"    Submissions    : {len(artifact.workspace['submissions'])}")
    print(f"    Grading Drafts : {len(artifact.workspace['grading_results'])}")

    # ── 3. Automated 12-Point Acceptance Suite ────────────────────────────────
    section("3. AUTOMATED 12-POINT ACCEPTANCE TEST SUITE: report = acceptance_suite(artifact, plan)")
    report = factory.run_acceptance_suite(artifact, plan_spec=plan_spec)

    print(f"  Test Evaluation Latency: {report.evaluation_time_ms:.2f} ms")
    print(f"  Total Acceptance Tests: {report.total_tests} | Passed: {report.passed_count} | Failed: {report.failed_count}\n")

    print(f"  {'ID':<16} {'Test Name':<42} {'Status':<10} {'Diagnostic Evidence'}")
    print("  " + "-" * 90)
    for t in report.tests:
        sym = "[PASS]" if t.passed else "[FAIL]"
        print(f"  {t.test_id:<16} {t.name:<42} {sym:<10} {t.diagnostic_evidence[:28]}...")

    # ── 4. Strict Human Gatekeeper ───────────────────────────────────────────
    section("4. FACULTY GATEKEEPER: require report.all_pass")
    gate_clean = factory.verify_and_advance_to_faculty(artifact)
    print(f"  Gate Authorization: {gate_clean.gate_status}")
    print(f"  Decision Detail   : {gate_clean.reason}")

    # Negative Test: Corrupted artifact blocked at gate
    print("\n  [Negative Test] Evaluating corrupted artifact (grade overflow 140/100)...")
    corrupted_artifact = artifact.model_copy(deep=True)
    corrupted_artifact.workspace["grading_results"][0]["final_score"] = 140.0
    gate_corrupted = factory.verify_and_advance_to_faculty(corrupted_artifact)
    print(f"  Gate Authorization: {gate_corrupted.gate_status}")
    print(f"  Decision Detail   : {gate_corrupted.reason}")

    # ── 5. Acceptance Checklist ──────────────────────────────────────────────
    section("5. ACCEPTANCE CRITERIA CHECKLIST")
    checks = {
        "One build command compiles full workspace": artifact.build_id is not None,
        "Automated 12-point acceptance suite evaluated": report.total_tests == 12,
        "100% green test report achieved on clean build": report.all_pass is True,
        "Human gate strictly blocks unverified outputs": gate_corrupted.authorized_for_faculty_review is False,
        "Verified artifacts advance to Faculty review": gate_clean.authorized_for_faculty_review is True,
        "Full SDLC provenance recorded in runtime audit": len(runtime.in_memory_audit) >= 1,
    }

    all_passed = all(checks.values())
    for label, passed in checks.items():
        sym = "[PASS]" if passed else "[FAIL]"
        print(f"  {sym} {label}")

    print(f"\n  Final Result: {'ALL LAB 11 CRITERIA PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
