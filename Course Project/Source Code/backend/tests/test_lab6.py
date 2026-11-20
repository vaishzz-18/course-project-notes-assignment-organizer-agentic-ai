"""
Acceptance Test Suite for Lab 6: Runtime — Skills, Tools, Memory, Audit
Verifies:
1. Complete audit logging with input/output provenance persisted to database.
2. Checkpoint creation with atomic versioning.
3. Crash & Resume: System resumes from exact last checkpoint after failure.
4. Budget enforcement: Over-budget step execution halts and escalates.
5. Human review gate: Hard stop prevents publishing without faculty approval.
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.governed_runtime import AURAControlledRuntime, RuntimeBudget


def test_lab6_audit_logging():
    """Acceptance Test 1: Full input/output provenance is logged for every action."""
    runtime = AURAControlledRuntime()
    run_id = "run_audit_test_01"

    entry = runtime.log_step(
        run_id=run_id,
        agent_name="NotesRepositoryAgent",
        action="fetch_unit_notes",
        inputs={"course_id": 1, "unit": "Unit 1"},
        outputs={"notes_count": 2, "status": "retrieved"},
        status="success",
        cost=15
    )

    assert entry.run_id == run_id
    assert entry.action == "fetch_unit_notes"
    assert entry.input_data["unit"] == "Unit 1"
    assert entry.output_data["notes_count"] == 2
    assert len(runtime.in_memory_audit) >= 1
    print(f"\n[PASS] Audit Logging verified: Entry {entry.entry_id} logged with inputs & outputs.")


def test_lab6_checkpoint_and_crash_resume():
    """Acceptance Test 2: Injected crash resumes cleanly from last checkpoint."""
    runtime = AURAControlledRuntime()
    run_id = "run_crash_test_02"

    # Step 1: Initialize
    runtime.checkpoint(run_id, "step_1_notes_loaded", {"notes_loaded": True, "count": 4})

    # Step 2: Ingest submissions & checkpoint
    saved_state = {
        "submissions_analyzed": ["alex_sub1", "priya_sub1"],
        "pending_similarity_check": True
    }
    cp2 = runtime.checkpoint(run_id, "step_2_submissions_analyzed", saved_state)
    assert cp2.version >= 2

    # SIMULATE SUDDEN CRASH (runtime instance destroyed)
    del runtime

    # RECOVERY: New runtime instance boots up and resumes run
    recovered_runtime = AURAControlledRuntime()
    resumed_data = recovered_runtime.resume_from_checkpoint(run_id)

    assert resumed_data["run_id"] == run_id
    assert resumed_data["step_name"] == "step_2_submissions_analyzed"
    assert resumed_data["state"]["submissions_analyzed"] == ["alex_sub1", "priya_sub1"]
    assert resumed_data["state"]["pending_similarity_check"] is True
    print(f"\n[PASS] Crash Recovery verified: Resumed from checkpoint '{resumed_data['step_name']}' at version {resumed_data['version']}.")


def test_lab6_budget_enforcement():
    """Acceptance Test 3: Exhausted budget triggers pause and escalation."""
    # Strict budget: max 3 steps
    strict_budget = RuntimeBudget(max_steps=3, max_cost_tokens=100)
    runtime = AURAControlledRuntime(budget=strict_budget)
    run_id = "run_budget_test_03"

    for i in range(1, 4):
        runtime.log_step(run_id, "SpecialistAgent", f"step_{i}", {"i": i}, {"res": "ok"}, cost=10)

    assert not runtime.is_paused

    # 4th step exceeds max_steps=3
    runtime.log_step(run_id, "SpecialistAgent", "step_4", {"i": 4}, {"res": "overflow"}, cost=10)
    
    assert runtime.is_paused
    assert "Budget exceeded" in runtime.pause_reason
    print(f"\n[PASS] Budget Enforcement verified: Paused and escalated -> {runtime.pause_reason}")


def test_lab6_human_approval_gate():
    """Acceptance Test 4: Consequential actions strictly stopped at human gate."""
    runtime = AURAControlledRuntime(gates=["faculty_approval_gate"])

    # Attempt publishing without faculty approval -> BLOCKED
    allowed_without_signoff = runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=False)
    assert not allowed_without_signoff, "Publishing must be blocked without faculty approval!"

    # Attempt with faculty approval -> ALLOWED
    allowed_with_signoff = runtime.check_human_gate("faculty_approval_gate", has_faculty_approval=True)
    assert allowed_with_signoff
    print("\n[PASS] Human Approval Gate verified: Hard stop enforced before publishing.")


if __name__ == "__main__":
    test_lab6_audit_logging()
    test_lab6_checkpoint_and_crash_resume()
    test_lab6_budget_enforcement()
    test_lab6_human_approval_gate()
    print("\nALL LAB 6 ACCEPTANCE TESTS PASSED!")
