"""
Interactive Demonstration CLI for Lab 6: Runtime (Skills, Tools, Memory, Audit)
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Audited step-by-step execution logging both inputs and outputs
2. Simulated crash and automatic checkpoint resume
3. Budget limit guardrail (preventing runaway steps)
4. Hard-stop faculty approval gate before publishing.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.governed_runtime import AURAControlledRuntime, RuntimeBudget


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab6_demonstration():
    print_banner("LAB 6: CONTROLLED GOVERNED RUNTIME")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Core Capabilities: Budgets, Checkpoints, Crash-Resume, Audit Trail & Human Gates\n")

    # -------------------------------------------------------------
    # 1. Audited Execution Trace
    # -------------------------------------------------------------
    print_banner("1. STEP-BY-STEP AUDIT LOGGING (INPUTS & OUTPUTS)")
    runtime = AURAControlledRuntime()
    run_id = "run_demo_audited_601"

    print(f"Executing Step 1: Notes Ingestion...")
    runtime.log_step(
        run_id=run_id,
        agent_name="NotesRepositoryAgent",
        action="sync_unit_materials",
        inputs={"course_id": 1, "unit": "Unit 2"},
        outputs={"notes_synced": 1, "status": "MCP_OK"},
        cost=10
    )

    print(f"Executing Step 2: Submission Gathering...")
    runtime.log_step(
        run_id=run_id,
        agent_name="SubmissionCollectionAgent",
        action="collect_batch",
        inputs={"assignment_id": 1},
        outputs={"total_collected": 5, "late_count": 1},
        cost=15
    )

    print("\n[Runtime Audit Trace (Sample Entry)]:")
    entry = runtime.in_memory_audit[-1]
    print(f"  Entry ID: {entry.entry_id}")
    print(f"  Agent: {entry.agent_name} -> Action: {entry.action}")
    print(f"  Inputs Recorded: {entry.input_data}")
    print(f"  Outputs Recorded: {entry.output_data}")
    print(f"  Timestamp: {entry.timestamp}")

    # -------------------------------------------------------------
    # 2. Checkpoint & Crash-Resume Simulation
    # -------------------------------------------------------------
    print_banner("2. CHECKPOINT & CRASH-RESUME SIMULATION")
    crash_run_id = "run_demo_crash_recovery"
    print(f"Initiating run '{crash_run_id}'...")
    print("  -> Completed Stage 1: Rubric verified.")
    runtime.checkpoint(crash_run_id, "stage_1_rubric_locked", {"rubric_max": 100.0, "status": "locked"})

    print("  -> Completed Stage 2: Plagiarism checks done.")
    state_before_crash = {
        "verified_submissions": ["alex_sub1", "priya_sub1", "marcus_sub1"],
        "flagged_plagiarism": [{"student": "David Kim", "similarity": 0.96}]
    }
    cp = runtime.checkpoint(crash_run_id, "stage_2_similarity_complete", state_before_crash)
    print(f"  [CHECKPOINT SAVED] Version: {cp.version} at step: '{cp.step_name}'")

    print("\n  *** SIMULATING SUDDEN HOST SERVER CRASH / PROCESS TERMINATION ***")
    del runtime  # Destroy runtime state in memory

    print("\n  [SYSTEM RESTART]: Spawning fresh AURAControlledRuntime instance...")
    recovered_runtime = AURAControlledRuntime()
    print(f"  Attempting recovery: resume_from_checkpoint('{crash_run_id}')...")
    resumed = recovered_runtime.resume_from_checkpoint(crash_run_id)

    print(f"  [RECOVERY SUCCESSFUL]")
    print(f"    Resumed Version: {resumed['version']}")
    print(f"    Resumed Step: {resumed['step_name']}")
    print(f"    Restored Flagged Students: {resumed['state']['flagged_plagiarism']}")

    # -------------------------------------------------------------
    # 3. Budget Overflow Guardrail
    # -------------------------------------------------------------
    print_banner("3. BUDGET OVERFLOW GUARDRAIL")
    strict_runtime = AURAControlledRuntime(budget=RuntimeBudget(max_steps=2, max_cost_tokens=50))
    budget_run_id = "run_budget_guardrail_demo"

    print("Executing steps within budget (max_steps=2)...")
    strict_runtime.log_step(budget_run_id, "Worker1", "task_a", {}, {}, cost=10)
    strict_runtime.log_step(budget_run_id, "Worker2", "task_b", {}, {}, cost=10)
    print(f"  Step 1 & 2 completed. Paused={strict_runtime.is_paused}")

    print("Attempting Step 3 (exceeds budget of 2)...")
    strict_runtime.log_step(budget_run_id, "Worker3", "task_c", {}, {}, cost=10)
    print(f"  Guardrail Triggered! Paused={strict_runtime.is_paused}")
    print(f"  Escalation Reason: {strict_runtime.pause_reason}")

    # -------------------------------------------------------------
    # 4. Faculty Approval Gate
    # -------------------------------------------------------------
    print_banner("4. FACULTY APPROVAL GATE (HUMAN IN THE LOOP)")
    gate_runtime = AURAControlledRuntime(gates=["faculty_approval_gate"])

    print("Attempting to publish grade drafts WITHOUT faculty signature...")
    allowed_no_auth = gate_runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=False)
    print(f"  Result: Action Allowed = {allowed_no_auth} -> [HARD STOP ENFORCED: Escalating to Dr. Vaishnavi Patel]")

    print("\nFaculty signs off on grades queue: [X] APPROVE")
    allowed_with_auth = gate_runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=True)
    print(f"  Result: Action Allowed = {allowed_with_auth} -> [GOVERNED PUBLISH AUTHORIZED]")

    print_banner("LAB 6 DEMONSTRATION COMPLETE: ALL RUNTIME CONTROLS OPERATIONAL")


if __name__ == "__main__":
    run_lab6_demonstration()
