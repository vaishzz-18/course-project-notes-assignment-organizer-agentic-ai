"""
Lab 9 Demo — Deep Research (Grounding & Evidence)
Chapter 2: Course Project, Notes & Assignment Organizer

Run:
    cd backend
    python lab9_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.grounding_agent import EvidenceGroundingAgent
from runtime.governed_runtime import AURAControlledRuntime

DIVIDER = "=" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def main():
    runtime = AURAControlledRuntime()
    agent = EvidenceGroundingAgent(runtime=runtime, coverage_threshold=0.50)

    print("\n" + "+------------------------------------------------------------------------+")
    print("|  LAB 9: DEEP RESEARCH -- Ground & Evidence Ledger                      |")
    print("|  Chapter 2: Course Project, Notes & Assignment Organizer               |")
    print("+------------------------------------------------------------------------+")
    print("\nCore Design Principle:")
    print("  'Every output maps to cited in-scope evidence; ungrounded items are rejected.'")
    print("\nPseudocode:")
    print("  for c in candidates:")
    print("      ev = research(c, source='the faculty-approved rubric and syllabus')")
    print("      if not ev.in_scope: reject(c)")
    print("      c.evidence = ev")

    # ── Sample Submissions ───────────────────────────────────────────────────
    section("1. INGESTING CANDIDATE SUBMISSIONS")
    sample_submissions = [
        {
            "id": "alex_001",
            "student_name": "Alex Chen",
            "student_id": 5,
            "title": "LangGraph StateGraph & ReAct Engine",
            "content": (
                "Implemented an agentic workflow using LangGraph StateGraph with explicit nodes and conditional edges. "
                "The planner loop executes ReAct reasoning cycles to clarify requirements and propose plans. "
                "Calculations call typed tools to enforce zero hallucination."
            )
        },
        {
            "id": "priya_002",
            "student_name": "Priya Sharma",
            "student_id": 6,
            "title": "Parallel Swarm Worker Architecture",
            "content": (
                "This submission implements a parallel swarm using asyncio.gather for fan-out processing of student tasks. "
                "The coordinator merges worker drafts strictly aligned to the locked course plan. "
                "StateGraph back-edges provide self-healing conditional retry routing."
            )
        },
        {
            "id": "marcus_003",
            "student_name": "Marcus Vance",
            "student_id": 7,
            "title": "Typed Tools with Pydantic Schema Validation",
            "content": (
                "We designed typed tools for deadline calculation and rubric checking using Pydantic schemas. "
                "The agent loop enforces zero hallucination math, ensuring grades and similarity scores are strictly tool-computed."
            )
        },
        {
            "id": "quantum_hallucination",
            "student_name": "Out-of-Scope Student 1",
            "student_id": 99,
            "title": "Quantum Annealing for Assignment Allocation",
            "content": (
                "We applied D-Wave quantum annealing adiabatic Hamiltonian physics to schedule course assignments. "
                "Superposition qubits collapse into optimal assignment slots."
            )
        },
        {
            "id": "blockchain_mining",
            "student_name": "Out-of-Scope Student 2",
            "student_id": 98,
            "title": "Decentralized Proof-of-Work Grade Ledger",
            "content": (
                "This project uses Ethereum smart contract blockchain mining to mint NFTs representing student grades. "
                "Miners validate hashes before distributing course tokens."
            )
        }
    ]

    for s in sample_submissions:
        print(f"  * Candidate [{s['id']}] by {s['student_name']}: '{s['title']}'")

    # ── Execute Research & Grounding Loop ────────────────────────────────────
    section("2. EXECUTING DEEP RESEARCH & GROUNDING LOOP")
    print("  Auditing candidate claims against faculty-approved syllabus & rubrics...")

    candidates, evidence_table = agent.evaluate_batch(
        submissions=sample_submissions,
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
        assignment_title="Assignment 1: Agentic Workflow Architecture"
    )

    for c in candidates:
        status_symbol = "[GROUNDED]" if c.status == "GROUNDED" else "[REJECTED]"
        print(f"\n  {status_symbol} {c.student_name} ({c.candidate_id})")
        print(f"    Coverage Score: {c.evidence.coverage_score * 100:.0f}%")
        print(f"    Verified Concepts: {', '.join(c.evidence.verified_concepts) if c.evidence.verified_concepts else 'None'}")
        if c.evidence.citations:
            print("    Evidence Citations:")
            for cit in c.evidence.citations[:2]:
                print(f"      - [{cit.source_type.upper()}] {cit.source_title}")
                print(f"        Quote: \"{cit.exact_quote[:75]}...\"")
        if c.status == "REJECTED":
            print(f"    Rejection Reason: {c.evidence.rejection_reason}")

    # ── Paper-Level Evidence Table ───────────────────────────────────────────
    section("3. PAPER-LEVEL EVIDENCE TABLE (LEDGER)")
    print(f"  Course: {evidence_table.course_code} - {evidence_table.course_name}")
    print(f"  Total Candidates: {evidence_table.total_candidates} | Grounded: {evidence_table.grounded_count} | Rejected: {evidence_table.rejected_count}")
    print(f"  Average Grounding Coverage: {evidence_table.average_coverage * 100:.1f}%\n")

    print(f"  {'ID':<22} {'Student':<20} {'Status':<12} {'Coverage':<10} {'Primary Source'}")
    print("  " + "-" * 78)
    for row in evidence_table.rows:
        print(f"  {row.candidate_id:<22} {row.student_name:<20} {row.status:<12} {row.coverage_score*100:>5.0f}%     {row.primary_source[:30]}")

    # ── Acceptance Checklist ─────────────────────────────────────────────────
    section("4. ACCEPTANCE CRITERIA CHECKLIST")
    checks = {
        "Every candidate carries an evidence record": all(c.evidence is not None for c in candidates),
        "A paper-level evidence table is produced": len(evidence_table.rows) == 5,
        "Every accepted output maps to an in-scope source": all(c.evidence.in_scope for c in candidates if c.status == "GROUNDED"),
        "Ungrounded/out-of-scope candidates are rejected": all(not c.evidence.in_scope for c in candidates if c.status == "REJECTED"),
        "Rejection reasons explicitly recorded": all(c.evidence.rejection_reason for c in candidates if c.status == "REJECTED"),
        "Governed by AURAControlledRuntime audit trace": len(runtime.in_memory_audit) >= 5,
    }

    all_passed = all(checks.values())
    for label, passed in checks.items():
        sym = "[PASS]" if passed else "[FAIL]"
        print(f"  {sym} {label}")

    print(f"\n  Final Result: {'ALL LAB 9 CRITERIA PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
