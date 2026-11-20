"""
Lab 6: Controlled Governed Runtime — Skills, Tools, Memory, Audit
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Run the agent inside a controlled runtime with strict budgets, atomic checkpoints,
crash-resume capability, and a tamper-proof audit trail.

Acceptance Criteria:
Every action is logged with inputs/outputs; a crashed run resumes from its last checkpoint.

Pseudocode:
run = Runtime(budget=B, gates=[publish])
for step in agent.loop():
    audit.log(step.intent, step.in, step.out)
    if step.cost > budget: pause_and_escalate()
    checkpoint(state)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import sqlite3
import uuid
from pathlib import Path


class RuntimeBudget(BaseModel):
    max_steps: int = 10
    max_cost_tokens: int = 50000
    timeout_seconds: float = 60.0


class CheckpointRecord(BaseModel):
    run_id: str
    step_name: str
    version: int
    state_payload: Dict[str, Any]
    checkpointed_at: str


class AuditEntry(BaseModel):
    entry_id: str
    run_id: str
    agent_name: str
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: str
    cost_units: int = 1
    timestamp: str


class AURAControlledRuntime:
    """
    Hardened Coordinator Runtime Controller:
    Wraps all specialist agents, skills, and tools in a safe, monitored sandbox.
    Enforces:
    - Step & resource budgets
    - Atomic state checkpointing
    - Crash recovery and resume
    - Audit logging of all inputs and outputs
    - Human approval gates
    """

    def __init__(self, budget: Optional[RuntimeBudget] = None, gates: Optional[List[str]] = None):
        self.budget = budget or RuntimeBudget()
        self.gates = gates or ["faculty_approval_gate", "grade_publish_gate"]
        self.db_path = Path(__file__).parent.parent.parent / "data" / "organizer.db"
        self.current_step = 0
        self.current_cost = 0
        self.is_paused = False
        self.pause_reason: Optional[str] = None
        self.in_memory_audit: List[AuditEntry] = []

    def _get_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Audit Logging ─────────────────────────────────────────────────────────

    def log_step(self, run_id: str, agent_name: str, action: str, inputs: dict, outputs: dict, status: str = "success", cost: int = 10) -> AuditEntry:
        """Logs action with complete input/output provenance to DB and runtime memory."""
        now_str = datetime.utcnow().isoformat()
        entry_id = f"aud_{uuid.uuid4().hex[:12]}"
        
        entry = AuditEntry(
            entry_id=entry_id,
            run_id=run_id,
            agent_name=agent_name,
            action=action,
            input_data=inputs,
            output_data=outputs,
            status=status,
            cost_units=cost,
            timestamp=now_str
        )
        self.in_memory_audit.append(entry)

        # Persist to SQLite audit_logs table
        conn = self._get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO audit_logs (run_id, agent_name, action, entity_type, entity_id, input_data, output_data, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, action, "runtime_step", self.current_step,
            json.dumps(inputs, default=str), json.dumps(outputs, default=str), status, now_str
        ))
        conn.commit()
        conn.close()

        # Update budget metrics
        self.current_step += 1
        self.current_cost += cost
        if self.current_step > self.budget.max_steps or self.current_cost > self.budget.max_cost_tokens:
            self.pause_and_escalate(run_id, f"Budget exceeded: steps={self.current_step}/{self.budget.max_steps}, cost={self.current_cost}/{self.budget.max_cost_tokens}")

        return entry

    # ── Checkpointing & Crash Resume ──────────────────────────────────────────

    def checkpoint(self, run_id: str, step_name: str, state_payload: Dict[str, Any]) -> CheckpointRecord:
        """Atomically checkpoints run state for crash recovery."""
        now_str = datetime.utcnow().isoformat()
        conn = self._get_db()
        c = conn.cursor()

        # Check existing version
        c.execute("SELECT version FROM run_contexts WHERE run_id = ?", (run_id,))
        row = c.fetchone()
        next_ver = (row["version"] + 1) if row else 1

        state_json = json.dumps({"step_name": step_name, "state": state_payload}, default=str)
        if row:
            c.execute("""
                UPDATE run_contexts
                SET state = ?, version = ?, attempts = attempts + 1
                WHERE run_id = ?
            """, (state_json, next_ver, run_id))
        else:
            c.execute("""
                INSERT INTO run_contexts (run_id, status, plan, state, version, attempts, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (run_id, "running", json.dumps({"plan_init": True}), state_json, next_ver, now_str))

        conn.commit()
        conn.close()

        return CheckpointRecord(
            run_id=run_id,
            step_name=step_name,
            version=next_ver,
            state_payload=state_payload,
            checkpointed_at=now_str
        )

    def resume_from_checkpoint(self, run_id: str) -> Dict[str, Any]:
        """Resumes state from the latest saved checkpoint after a crash."""
        conn = self._get_db()
        c = conn.cursor()
        c.execute("SELECT run_id, status, state, version, attempts FROM run_contexts WHERE run_id = ?", (run_id,))
        row = c.fetchone()
        conn.close()

        if not row or not row["state"]:
            raise ValueError(f"No checkpoint found for run_id: {run_id}")

        checkpoint_data = json.loads(row["state"])
        self.log_step(
            run_id=run_id,
            agent_name="AURAControlledRuntime",
            action="resume_from_checkpoint",
            inputs={"resumed_version": row["version"], "prior_step": checkpoint_data.get("step_name")},
            outputs={"resumed_state": checkpoint_data.get("state")},
            status="resumed",
            cost=5
        )
        return {
            "run_id": run_id,
            "status": row["status"],
            "version": row["version"],
            "step_name": checkpoint_data.get("step_name"),
            "state": checkpoint_data.get("state")
        }

    # ── Governance & Human Approval Gates ─────────────────────────────────────

    def pause_and_escalate(self, run_id: str, reason: str):
        """Hard stop: Pauses execution and escalates to Course Faculty."""
        self.is_paused = True
        self.pause_reason = reason
        conn = self._get_db()
        c = conn.cursor()
        c.execute("UPDATE run_contexts SET status = 'escalated' WHERE run_id = ?", (run_id,))
        conn.commit()
        conn.close()

    def check_human_gate(self, gate_name: str, has_faculty_approval: bool) -> bool:
        """Enforces human review gate before publishing."""
        if gate_name in self.gates and not has_faculty_approval:
            return False
        return True
