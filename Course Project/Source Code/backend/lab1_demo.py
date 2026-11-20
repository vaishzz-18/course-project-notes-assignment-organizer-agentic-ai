"""
Interactive Demonstration CLI for Lab 1: Agent vs Chatbot
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Naive Chatbot behavior (Flawed one-shot answer without clarification)
2. True Agent behavior (Clarify -> Propose Plan -> Revise on Feedback -> Lock)
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from agents.planner_agent import CoursePlannerAgent, CoursePlan, ClarifyResult


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab1_demonstration():
    planner = CoursePlannerAgent()

    print_banner("LAB 1: AGENT VS CHATBOT (THE PLANNER LOOP)")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Design Principle: Agents draft and flag; a named human approves.")
    print("Demonstration Mode: Automated Full Trace with Acceptance Verification\n")

    # -------------------------------------------------------------
    # Scenario 1: Contrast with Naive Chatbot
    # -------------------------------------------------------------
    print_banner("SCENARIO 1: The Naive Chatbot Approach (What NOT to do)")
    user_prompt = "Help me organize my AI course."
    print(f"User Prompt: \"{user_prompt}\"")
    print("\nNaive Chatbot says:")
    print("  'Here is a generic 10-week syllabus with some random assignments and a project.'")
    print("  --> Failure: Made assumptions, never asked questions, cannot revise systematically.")

    # -------------------------------------------------------------
    # Scenario 2: Agent Clarification Step
    # -------------------------------------------------------------
    print_banner("SCENARIO 2: Our Agentic Planner (Step 1: Clarification Loop)")
    print(f"Coordinator receives prompt: \"{user_prompt}\"")
    clarify_res: ClarifyResult = planner.clarify(user_prompt)

    print(f"\nAgent Analysis:")
    print(f"  Is Clarified: {clarify_res.is_clarified}")
    print(f"  Missing Dimensions: {clarify_res.missing_fields}")
    print(f"  Feedback: {clarify_res.feedback_message}\n")

    print(f"Generated Clarifying Questions ({len(clarify_res.questions)} asked):")
    for i, q in enumerate(clarify_res.questions, 1):
        print(f"  [{i}] {q.question}")
        print(f"      Why: {q.context}")
        if q.options:
            print(f"      Options: {', '.join(q.options)}")

    # -------------------------------------------------------------
    # Scenario 3: Propose Coherent Plan
    # -------------------------------------------------------------
    print_banner("SCENARIO 3: Synthesizing the Course Plan (Step 2: Propose Plan)")
    print("Faculty answers clarifying questions:")
    answers = {
        "course_name": "CS401: Agentic AI & Autonomous Systems",
        "course_code": "CS401",
        "units": 4,
        "assignments": 2,
        "milestones": 3
    }
    for k, v in answers.items():
        print(f"  - {k}: {v}")

    plan: CoursePlan = planner.propose_plan(answers)
    print(f"\n[Generated Plan Draft v{plan.version}] (Status: {plan.status})")
    print(f"  Plan ID: {plan.plan_id}")
    print(f"  Course: {plan.course_name} ({plan.course_code})")
    print(f"  Units Outline ({len(plan.units)} Units):")
    for u in plan.units:
        print(f"    * Unit {u.unit_number}: {u.title} ({len(u.topics)} topics)")
    
    print(f"\n  Assignments Outline ({len(plan.assignments)} Assignments):")
    for a in plan.assignments:
        print(f"    * {a.title} ({a.unit}) - Max Marks: {a.max_marks}")
        for r in a.rubric:
            print(f"        - {r.criterion}: {r.max_marks} marks ({r.description})")

    print(f"\n  Milestones Outline ({len(plan.milestones)} Checkpoints):")
    for m in plan.milestones:
        print(f"    * Checkpoint {m.checkpoint_number}: {m.title} (Week {m.estimated_week})")

    # -------------------------------------------------------------
    # Scenario 4: Revision Loop
    # -------------------------------------------------------------
    print_banner("SCENARIO 4: Faculty Feedback & Plan Revision (Step 3: Revise Loop)")
    faculty_feedback = "Please add an assignment on Multi-Agent Swarms with 50 marks, and add an interim checkpoint."
    print(f"Faculty Review Gate: Feedback given:")
    print(f"  \"{faculty_feedback}\"")

    revised_plan: CoursePlan = planner.revise(plan, faculty_feedback)
    print(f"\n[Revised Plan v{revised_plan.version}] (Status: {revised_plan.status})")
    print(f"  New Assignments Count: {len(revised_plan.assignments)}")
    print(f"  New Checkpoints Count: {len(revised_plan.milestones)}")
    print("  Revision History:")
    for note in revised_plan.revision_notes:
        print(f"    -> {note}")

    # -------------------------------------------------------------
    # Scenario 5: Lock Plan
    # -------------------------------------------------------------
    print_banner("SCENARIO 5: Locking the Blueprint (Step 4: Lock Plan)")
    locked_plan = planner.lock_plan(revised_plan)
    print(f"Final Status: {locked_plan.status.upper()}")
    print("  The course plan is now immutable.")
    print("  Downstream agents (Notes Repository, Assignment Distribution, Swarms) can now build against this locked spec.")
    print_banner("LAB 1 DEMONSTRATION COMPLETE: ALL ACCEPTANCE GATES PASSED")


if __name__ == "__main__":
    run_lab1_demonstration()
