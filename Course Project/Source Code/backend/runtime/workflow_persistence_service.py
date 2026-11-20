"""
WorkflowPersistenceService — Persistent checkpointer for LangGraph StateGraph execution.
Persists execution state in the WorkflowThread database table across process restarts,
supporting genuine human-in-the-loop pause, inspection, approval, and resumption.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "organizer.db"


class WorkflowPersistenceService:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def save_checkpoint(
        self,
        thread_id: str,
        run_id: str,
        current_node: str,
        state: Dict[str, Any],
        status: str = "running",
        approval_status: Optional[str] = None,
        error_info: Optional[str] = None,
    ) -> str:
        """Saves or updates a workflow thread checkpoint."""
        conn = self._get_conn()
        c = conn.cursor()
        now_str = datetime.now(timezone.utc).isoformat()
        state_clean = json.dumps(state, default=str)

        # Check if thread exists
        c.execute("SELECT id FROM workflow_threads WHERE thread_id = ?", (thread_id,))
        row = c.fetchone()

        if row:
            c.execute(
                """
                UPDATE workflow_threads
                SET current_node = ?, workflow_status = ?, state_json = ?, approval_status = ?, error_info = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (current_node, status, state_clean, approval_status, error_info, now_str, thread_id),
            )
        else:
            c.execute(
                """
                INSERT INTO workflow_threads
                (thread_id, run_id, agent_name, current_node, workflow_status, state_json, approval_status, error_info, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    run_id,
                    "AURAOrchestrator",
                    current_node,
                    status,
                    state_clean,
                    approval_status,
                    error_info,
                    now_str,
                    now_str,
                ),
            )
        conn.commit()
        conn.close()
        return thread_id

    def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Loads a persisted checkpoint from the database."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM workflow_threads WHERE thread_id = ?", (thread_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        if d.get("state_json"):
            try:
                d["state"] = json.loads(d["state_json"])
            except Exception:
                d["state"] = {}
        return d

    def record_approval_and_resume(self, thread_id: str, approver_id: int) -> Dict[str, Any]:
        """Records human approval and marks the thread ready to advance."""
        conn = self._get_conn()
        c = conn.cursor()
        now_str = datetime.now(timezone.utc).isoformat()
        c.execute(
            """
            UPDATE workflow_threads
            SET approval_status = 'approved', workflow_status = 'resumed', updated_at = ?
            WHERE thread_id = ?
            """,
            (now_str, thread_id),
        )
        conn.commit()
        conn.close()
        checkpoint = self.load_checkpoint(thread_id)
        if checkpoint and "state" in checkpoint:
            checkpoint["state"]["human_approved"] = True
            checkpoint["state"]["pipeline_status"] = "approved_by_faculty"
            self.save_checkpoint(
                thread_id=thread_id,
                run_id=checkpoint.get("run_id", ""),
                current_node="node_faculty_gate",
                state=checkpoint["state"],
                status="approved",
                approval_status="approved",
            )
        return checkpoint
