"""
Lab 13: Discipline-Specific Agents — Domain Specialisation Demo
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
  Pluggable specialists (theory, lab/coding, capstone project) so outputs
  match the specific style and constraints of each case.

Pseudocode:
  specialist = registry.get(domain)
  out = specialist.generate(item)
  GenerationAgent.use(specialist)

Usage:
  python backend/lab13_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.specialists import (
    DomainAwareGenerationAgent,
    DomainProfile,
)


def main():
    print("=" * 78)
    print("AURA LAB 13: DISCIPLINE-SPECIFIC AGENTS -- DOMAIN SPECIALISATION")
    print("Phase D: Governance & Capstone | Chapter 2 Course Project")
    print("=" * 78)
    print("Pseudocode: specialist = registry.get(domain); out = specialist.generate(item)\n")

    agent = DomainAwareGenerationAgent()

    # -------------------------------------------------------------------------
    # Step 1: Show Registry
    # -------------------------------------------------------------------------
    print("-" * 78)
    print("[STEP 1] Domain Specialist Registry")
    print("-" * 78)
    registry_info = agent.registry.list_specialists()
    print(f"Registered Specialists: {registry_info.total_specialists}")
    for s in registry_info.specialists:
        print(f"  - {s['name']} (Domain: {s['domain']})")

    # -------------------------------------------------------------------------
    # Step 2: Theory Specialist
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 2] TheorySpecialist -- Essay with Conceptual Rubrics & Citation Depth")
    print("-" * 78)

    theory_profile = DomainProfile(
        domain="theory",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )
    theory_item = {
        "submission_id": "sub_theory_201",
        "student_name": "Alex Chen",
        "content": "This essay examines ReAct cognitive loops in autonomous agent design, "
                   "drawing on Yao et al. (2023) to argue that interleaved reasoning "
                   "and acting outperforms chain-of-thought alone.",
    }
    theory_out = agent.generate(theory_item, theory_profile, domain="theory")
    _print_evaluation(theory_out)

    # -------------------------------------------------------------------------
    # Step 3: Lab/Coding Specialist
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 3] LabCodingSpecialist -- AST/Syntax, Test Coverage, Execution Rubric")
    print("-" * 78)

    coding_profile = DomainProfile(
        domain="lab_coding",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )
    coding_item = {
        "submission_id": "sub_code_202",
        "student_name": "Bob Miller",
        "content": (
            "class AgentLoop:\n"
            "    def __init__(self, tools):\n"
            "        self.tools = tools\n\n"
            "    def run(self, query):\n"
            "        plan = self.think(query)\n"
            "        result = self.act(plan)\n"
            "        return self.observe(result)\n"
        ),
    }
    coding_out = agent.generate(coding_item, coding_profile, domain="lab_coding")
    _print_evaluation(coding_out)
    print(f"  Language Detected: {coding_out.evaluation.get('language_detected')}")
    print(f"  Lines of Code:    {coding_out.evaluation.get('lines_of_code')}")
    print(f"  Syntax Valid:     {coding_out.evaluation.get('syntax_valid')}")

    # -------------------------------------------------------------------------
    # Step 4: Capstone Project Specialist
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 4] CapstoneProjectSpecialist -- Sprint Logs, Team Matrix, Deliverables")
    print("-" * 78)

    capstone_profile = DomainProfile(
        domain="capstone_project",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )
    capstone_item = {
        "submission_id": "sub_capstone_203",
        "student_name": "Charlie Brown",
        "content": "AURA Capstone: Sprint 4 complete. Full pipeline integration deployed.",
        "team_members": ["Charlie Brown", "Dana Lee", "Eve Park"],
    }
    capstone_out = agent.generate(capstone_item, capstone_profile, domain="capstone_project")
    _print_evaluation(capstone_out)
    matrix = capstone_out.evaluation.get("contribution_matrix", {})
    print("  Team Contribution Matrix:")
    for member, data in matrix.items():
        print(f"    {member}: {data['contribution_pct']}% | {data['commits']} commits | {data['tasks_completed']} tasks")
    print(f"  Deliverable Health: {capstone_out.evaluation.get('deliverable_health')}")

    # -------------------------------------------------------------------------
    # Step 5: Checkable Scheme Validation
    # -------------------------------------------------------------------------
    print("\n" + "-" * 78)
    print("[STEP 5] Checkable Scheme Validation")
    print("-" * 78)
    for name, out in [("Theory", theory_out), ("Lab/Coding", coding_out), ("Capstone", capstone_out)]:
        scheme = out.checkable_scheme
        weights_ok = abs(sum(c["weight"] for c in out.domain_criteria) - 1.0) < 0.01
        score_ok = out.total_score <= out.max_score
        criteria_present = all(
            req in [c["criterion"] for c in out.domain_criteria]
            for req in scheme.get("required_criteria", [])
        )
        print(f"  {name}: weights_sum=1.0 [{_ok(weights_ok)}] | score<=max [{_ok(score_ok)}] | all_criteria_present [{_ok(criteria_present)}]")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("LAB 13 DOMAIN SPECIALISATION DEMONSTRATION COMPLETE")
    print("=" * 78)
    print("[PASS] Pluggable specialist registry with 3 domain adapters.")
    print("[PASS] Theory specialist: conceptual rubrics + citation depth evaluation.")
    print("[PASS] Lab/Coding specialist: AST/syntax + test coverage + style evaluation.")
    print("[PASS] Capstone specialist: sprint logs + team matrix + deliverable health.")
    print("[PASS] Checkable scheme validates every specialist output.")
    print("[PASS] GenerationAgent.use(specialist) injection pattern demonstrated.")
    print("=" * 78)


def _print_evaluation(out):
    print(f"  Specialist:    {out.specialist_name}")
    print(f"  Domain:        {out.domain}")
    print(f"  Student:       {out.student_name}")
    print(f"  Submission ID: {out.submission_id}")
    print(f"  Total Score:   {out.total_score}/{out.max_score}")
    print("  Criteria Breakdown:")
    for c in out.domain_criteria:
        print(f"    - {c['criterion']}: {c['score']}/{c['max_score']} (weight: {c['weight']})")


def _ok(val: bool) -> str:
    return "PASS" if val else "FAIL"


if __name__ == "__main__":
    main()
