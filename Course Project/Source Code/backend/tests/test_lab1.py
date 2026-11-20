"""
Acceptance Test Suite for Lab 1: Agent vs Chatbot — The Planner Loop
Verifies:
1. Agent asks at least 2 clarifying questions when given a vague request.
2. Agent produces a structured, editable CoursePlan once clarified.
3. Agent performs iterative revisions based on faculty feedback.
4. Agent locks the plan into an immutable specification for subsequent labs.
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.planner_agent import CoursePlannerAgent, CoursePlan, ClarifyResult


def test_lab1_vague_request_asks_clarifying_questions():
    """Acceptance Test 1: Given a vague request, asks at least 2 clarifying questions."""
    planner = CoursePlannerAgent()
    vague_prompt = "Help me organize my AI course."
    
    result: ClarifyResult = planner.clarify(vague_prompt)
    
    assert not result.is_clarified, "Vague request should NOT be marked as clarified."
    assert len(result.questions) >= 2, f"Must ask at least 2 clarifying questions, got {len(result.questions)}"
    print(f"\n[PASS] Agent correctly asked {len(result.questions)} clarifying questions:")
    for i, q in enumerate(result.questions, 1):
        print(f"  {i}. {q.question}")


def test_lab1_clarified_context_produces_coherent_plan():
    """Acceptance Test 2: Given clarified answers, agent produces a structured, editable CoursePlan."""
    planner = CoursePlannerAgent()
    clarified_context = {
        "course_name": "Agentic AI & Autonomous Systems",
        "course_code": "CS401",
        "units": 4,
        "assignments": 2,
        "milestones": 3,
        "rubric": "100 marks standard"
    }
    
    plan: CoursePlan = planner.propose_plan(clarified_context)
    
    assert plan.plan_id.startswith("plan_")
    assert plan.course_code == "CS401"
    assert len(plan.units) == 4
    assert len(plan.assignments) >= 2
    assert len(plan.milestones) == 3
    assert plan.status == "draft"
    assert plan.version == 1
    print("\n[PASS] Coherent plan outline synthesized successfully.")
    print(f"  Course: {plan.course_name} ({plan.course_code})")
    print(f"  Units: {len(plan.units)}, Assignments: {len(plan.assignments)}, Milestones: {len(plan.milestones)}")


def test_lab1_revision_loop():
    """Acceptance Test 3: Agent revises plan based on faculty feedback and increments version."""
    planner = CoursePlannerAgent()
    initial_plan = planner.propose_plan({"course_name": "CS401", "course_code": "CS401"})
    
    # Faculty feedback: Add an extra assignment for multi-agent swarms
    revised_plan = planner.revise(initial_plan, "Please add an assignment on Multi-Agent Swarms with 50 marks.")
    
    assert revised_plan.version == 2
    assert revised_plan.status == "revised"
    assert len(revised_plan.assignments) == len(initial_plan.assignments) + 1
    assert any("Swarm" in a.title for a in revised_plan.assignments)
    assert len(revised_plan.revision_notes) >= 2
    print(f"\n[PASS] Plan successfully revised to version {revised_plan.version}.")
    print(f"  Latest Revision Note: {revised_plan.revision_notes[-1]}")


def test_lab1_lock_plan():
    """Acceptance Test 4: Agent locks plan into an immutable specification."""
    planner = CoursePlannerAgent()
    plan = planner.propose_plan({"course_name": "CS401", "course_code": "CS401"})
    locked = planner.lock_plan(plan)
    
    assert locked.status == "locked"
    assert "locked by Course Faculty" in locked.revision_notes[-1]
    print("\n[PASS] Plan successfully locked for downstream orchestration.")


if __name__ == "__main__":
    test_lab1_vague_request_asks_clarifying_questions()
    test_lab1_clarified_context_produces_coherent_plan()
    test_lab1_revision_loop()
    test_lab1_lock_plan()
    print("\nALL LAB 1 ACCEPTANCE TESTS PASSED!")
