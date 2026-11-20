"""
Enhanced Multi-Account Comprehensive Seed Script
Populates rich dummy data for:
- Faculty 1: Dr. Vaishnavi Patel (faculty@aura.edu) -> Course CS401
- Faculty 2: Vaish (vaishp1881@gmail.com) -> Course CS402 (Distributed Agent Architectures)
- Faculty 3: Pooja (pooja@gmail.com) -> Course CS403 (Safe & Governed Autonomous AI)
- Students:
  - Alex Chen (alex@aura.edu)
  - Priya Sharma (priya@aura.edu)
  - Marcus Vance (marcus@aura.edu)
  - Elena Rostova (elena@aura.edu)
  - David Kim (david@aura.edu)
  - Vaish Student (vaish@gmail.com)
  - Mike (mike@gmail.com)

Includes:
- Notes with full text content and version chains
- Assignments with structured multi-criterion rubrics
- Student Submissions with code files
- Published & Pending Grades with rubric breakdowns and feedback
- Project Groups & Student Group Memberships
- Milestones & Milestone Progress with green/amber/red health indicators
- Universal easy password: password123
"""
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_PATH = Path("D:/Sem 7/AGENTIC AI/PROJ/AGENTICAIAG1/data/organizer.db")
NOTES_DIR = Path("D:/Sem 7/AGENTIC AI/PROJ/AGENTICAIAG1/data/notes")
SUB_DIR = Path("D:/Sem 7/AGENTIC AI/PROJ/AGENTICAIAG1/data/submissions")

NOTES_DIR.mkdir(parents=True, exist_ok=True)
SUB_DIR.mkdir(parents=True, exist_ok=True)

def populate_all():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    universal_pwd = pwd_context.hash("password123")

    print("[1] Updating all passwords to password123...")
    c.execute("UPDATE users SET password_hash = ?", (universal_pwd,))
    conn.commit()

    # -------------------------------------------------------------
    # 2. Ensure Additional Courses for Faculty 1 and 2
    # -------------------------------------------------------------
    print("[2] Setting up courses across all faculty...")
    # Faculty IDs:
    # 1: Vaish (vaishp1881@gmail.com)
    # 2: pooja (pooja@gmail.com)
    # 4: Dr. Vaishnavi Patel (faculty@aura.edu)

    courses_to_add = [
        (2, "Distributed Agent Architectures", "CS402", "Advanced multi-agent coordination, Swarms, Consensus protocols, and Kafka streaming pipelines.", 1),
        (3, "Safe & Governed Autonomous AI", "CS403", "AI alignment, deterministic guardrails, LangGraph human-in-the-loop review nodes, and audit trails.", 2),
    ]
    for cid, name, code, desc, fac_id in courses_to_add:
        c.execute("SELECT id FROM courses WHERE id = ?", (cid,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO courses (id, name, code, description, faculty_id, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (cid, name, code, desc, fac_id))
    conn.commit()

    # -------------------------------------------------------------
    # 3. Enroll ALL students across courses
    # -------------------------------------------------------------
    print("[3] Enrolling all students into all courses...")
    all_student_ids = [3, 5, 6, 7, 8, 9, 10]
    for course_id in [1, 2, 3]:
        for sid in all_student_ids:
            c.execute("SELECT id FROM course_enrollments WHERE course_id = ? AND student_id = ?", (course_id, sid))
            if not c.fetchone():
                c.execute("""
                    INSERT INTO course_enrollments (course_id, student_id, enrolled_at)
                    VALUES (?, ?, datetime('now'))
                """, (course_id, sid))
    conn.commit()

    # -------------------------------------------------------------
    # 4. Rich Course Notes across courses
    # -------------------------------------------------------------
    print("[4] Generating rich notes for all courses...")
    notes_data = [
        # CS401 Notes
        (1, "Lecture 1: Foundations of Agentic AI", "Unit 1", "Agent Architecture", "unit1_foundations_v1.txt", "Unit 1: Agentic Foundations (v1)\nAgent definition: Perception, Reasoning, Action loop.", 1, 0, None, 4),
        (1, "Lecture 1: Foundations of Agentic AI (v2)", "Unit 1", "Agent Architecture", "unit1_foundations_v2.txt", "Unit 1: Agentic Foundations (v2)\nDetailed ReAct trace decomposition, reflection loops, and tool execution.", 2, 1, 1, 4),
        (1, "Lecture 2: MCP & Typed Tool Execution", "Unit 2", "MCP Protocol", "unit2_mcp_tools.txt", "Unit 2: FastMCP Tools\nStandardized JSON-RPC protocol for decoupling tool servers from LLM planners.", 1, 1, None, 4),
        (1, "Lecture 3: LangGraph Orchestration", "Unit 3", "State Graphs", "unit3_langgraph.txt", "Unit 3: LangGraph StateGraphs\nState management, retry back-edges, and faculty approval gates.", 1, 1, None, 4),
        (1, "Lecture 4: Swarm Multi-Agent Systems", "Unit 4", "Swarm Fan-Out", "unit4_swarms.txt", "Unit 4: Multi-Agent Parallel Swarms\nAsyncio.gather fan-out / fan-in worker pools with plan-aligned merge.", 1, 1, None, 4),

        # CS402 Notes (Vaish)
        (2, "Unit 1: Distributed Coordination Basics", "Unit 1", "Agent Communication", "cs402_u1.txt", "Communication protocols for distributed agents: RPC vs message queues.", 1, 1, None, 1),
        (2, "Unit 2: Leader Election & Consensus", "Unit 2", "Consensus Algorithms", "cs402_u2.txt", "Raft and Paxos for decentralized decision making among autonomous agent nodes.", 1, 1, None, 1),
        (2, "Unit 3: Scalable Vector Stores & Sharding", "Unit 3", "Distributed Memory", "cs402_u3.txt", "Distributed vector indexing and federated retrieval across multiple knowledge stores.", 1, 1, None, 1),

        # CS403 Notes (Pooja)
        (3, "Unit 1: AI Governance Frameworks", "Unit 1", "Deterministic Guardrails", "cs403_u1.txt", "Principles of AI safety: non-bypassable human review gates and provenance logging.", 1, 1, None, 2),
        (3, "Unit 2: Budgeting & Resource Bounds", "Unit 2", "Cost & Step Limits", "cs403_u2.txt", "Preventing runaway infinite loops through strict token, cost, and step budgets.", 1, 1, None, 2),
    ]

    for cid, title, unit, topic, fname, text, ver, is_curr, parent_id, uploader in notes_data:
        fpath = NOTES_DIR / fname
        fpath.write_text(text, encoding="utf-8")
        c.execute("SELECT id FROM notes WHERE file_name = ?", (fname,))
        row = c.fetchone()
        if not row:
            c.execute("""
                INSERT INTO notes (course_id, title, unit, topic, file_path, file_name, version, is_current, parent_id, uploaded_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (cid, title, unit, topic, str(fpath), fname, ver, is_curr, parent_id, uploader))
    conn.commit()

    # -------------------------------------------------------------
    # 5. Assignments across courses
    # -------------------------------------------------------------
    print("[5] Generating assignments with rubrics...")
    assignments_data = [
        # Course 1 (Dr. Vaishnavi Patel)
        (1, 1, "Assignment 1: Build a Tool-Using ReAct Agent",
         "Design and implement an autonomous ReAct agent with at least 3 typed tools, deadline validation, and similarity detection.",
         {
             "code_correctness": {"max": 40, "description": "Accurate tool invocation and valid output generation"},
             "react_loop_reasoning": {"max": 25, "description": "Clear thought-action-observation trace in logs"},
             "error_handling": {"max": 20, "description": "Graceful recovery and retry logic"},
             "documentation": {"max": 15, "description": "Architecture diagram and clean comments"}
         }, 100.0, datetime.utcnow() + timedelta(days=5), "published", 4),

        (2, 1, "Assignment 2: LangGraph Orchestration Pipeline",
         "Implement a 9-node LangGraph StateGraph pipeline with self-healing retry logic and a faculty approval gate.",
         {
             "state_management": {"max": 30, "description": "Immutable state progression across all 9 nodes"},
             "back_edge_retry": {"max": 30, "description": "Automatic retry transition when validation fails"},
             "human_gate": {"max": 25, "description": "Blocking gate halting pipeline until faculty signs off"},
             "testing": {"max": 15, "description": "Unit test coverage for state invariants"}
         }, 100.0, datetime.utcnow() + timedelta(days=12), "published", 4),

        # Course 2 (Vaish)
        (3, 2, "Assignment 1: Parallel Swarm & Fan-In Aggregation",
         "Build a concurrent worker pool using asyncio.gather to process multiple submission payloads in parallel.",
         {
             "concurrency": {"max": 50, "description": "True concurrent non-blocking execution"},
             "benchmark": {"max": 30, "description": "Accurate parallel vs sequential speedup metric"},
             "merge_integrity": {"max": 20, "description": "Clean fan-in merge into structured draft"}
         }, 100.0, datetime.utcnow() + timedelta(days=7), "published", 1),

        # Course 3 (Pooja)
        (4, 3, "Assignment 1: Governed Agent Runtime & Auditing",
         "Build an execution wrapper enforcing step budgets, crash-recovery checkpoints, and tamper-evident audit logging.",
         {
             "budget_control": {"max": 40, "description": "Enforce step, token, and time limits"},
             "checkpointing": {"max": 35, "description": "Atomic state saving and crash resume"},
             "audit_trail": {"max": 25, "description": "Provenance logging of all inputs and outputs"}
         }, 100.0, datetime.utcnow() + timedelta(days=9), "published", 2),
    ]

    for aid, cid, title, desc, rubric, max_m, due, status, creator in assignments_data:
        c.execute("SELECT id FROM assignments WHERE id = ?", (aid,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO assignments (id, course_id, title, description, rubric, max_marks, due_date, status, created_by, created_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (aid, cid, title, desc, json.dumps(rubric), max_m, due.isoformat(), status, creator))
    conn.commit()

    # -------------------------------------------------------------
    # 6. Submissions for all students
    # -------------------------------------------------------------
    print("[6] Creating submissions for all students...")
    # Student IDs:
    # 3: vaish (vaish@gmail.com)
    # 5: Alex Chen (alex@aura.edu)
    # 6: Priya Sharma (priya@aura.edu)
    # 7: Marcus Vance (marcus@aura.edu)
    # 8: Elena Rostova (elena@aura.edu)
    # 9: David Kim (david@aura.edu)
    # 10: mike (mike@gmail.com)

    submissions_specs = [
        # (sub_id, assignment_id, student_id, fname, code_snippet, is_late, sim_score, sim_flags)
        (1, 1, 5, "alex_sub1.txt", "class ReActAgent:\n    def __init__(self, tools):\n        self.tools = tools\n    def run(self, q): return self.tools[0].call(q)", False, 0.12, []),
        (2, 1, 6, "priya_sub1.txt", "class PriyaReAct:\n    def step(self, q):\n        return {'status': 'success', 'data': 'computed'}", False, 0.15, []),
        (3, 1, 7, "marcus_sub1.txt", "def marcus_agent(query): return 'Marcus ReAct Result'", True, 0.08, []),
        (4, 1, 8, "elena_sub1.txt", "class ElenaNodeGraph:\n    def execute(self, state): return state", False, 0.18, []),
        (5, 1, 9, "david_sub1.txt", "class ReActAgent:\n    def __init__(self, tools):\n        self.tools = tools\n    def run(self, q): return self.tools[0].call(q)", False, 0.96, [{"compared_to": "Alex Chen", "similarity": 0.9626, "risk": True}]),
        
        # Vaish Student (ID 3)
        (6, 1, 3, "vaish_sub1.txt", "class VaishAgent:\n    '''Autonomous ReAct agent with bounded loop and fallback.'''\n    def run(self, prompt):\n        return {'status': 'complete', 'answer': 'Safe reasoning trace'}", False, 0.11, []),
        (7, 2, 3, "vaish_asgn2.txt", "class StateGraphPipeline:\n    def __init__(self): self.nodes = []\n    def run(self): return 'Pipeline completed'", False, 0.14, []),
        (8, 3, 3, "vaish_swarm.txt", "async def run_swarm(workers): return await asyncio.gather(*workers)", False, 0.09, []),

        # Mike Student (ID 10)
        (9, 1, 10, "mike_sub1.txt", "def solve_ai_agent(p): return 'Mike solution on time'", False, 0.10, []),
        (10, 3, 10, "mike_swarm.txt", "import asyncio\nasync def fan_out(tasks): return await asyncio.gather(*tasks)", False, 0.13, []),

        # Alex on Assignment 2
        (11, 2, 5, "alex_langgraph.txt", "from langgraph.graph import StateGraph\ng = StateGraph(dict)\ng.add_node('ingest', lambda s: s)", False, 0.12, []),
        # Priya on Assignment 2
        (12, 2, 6, "priya_langgraph.txt", "from langgraph.graph import StateGraph\ngraph = StateGraph(dict)", False, 0.15, []),
    ]

    for sid_sub, asgn_id, stud_id, fname, code, is_late, sim_score, flags in submissions_specs:
        fpath = SUB_DIR / fname
        fpath.write_text(code, encoding="utf-8")
        c.execute("SELECT id FROM submissions WHERE id = ?", (sid_sub,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO submissions (id, assignment_id, student_id, file_path, file_name, submitted_at, is_late, similarity_score, similarity_flags, status)
                VALUES (?, ?, ?, ?, ?, datetime('now', '-2 days'), ?, ?, ?, 'submitted')
            """, (sid_sub, asgn_id, stud_id, str(fpath), fname, 1 if is_late else 0, sim_score, json.dumps(flags)))
    conn.commit()

    # -------------------------------------------------------------
    # 7. Rich Grades (Draft, Pending Approval, and Published)
    # -------------------------------------------------------------
    print("[7] Populating complete grades with rubric breakdowns...")
    grades_data = [
        # (submission_id, draft_m, draft_feedback, rubric_breakdown, final_m, final_feedback, status, approver)
        (1, 88.0, "Excellent modular implementation of ReAct loop. Thought-Action-Observation trace is clear.",
         {"code_correctness": 38, "react_loop_reasoning": 23, "error_handling": 15, "documentation": 12},
         88.0, "Approved. Clean code and well documented.", "published", 4),

        (2, 92.0, "Superb error handling and clean tool abstractions. Exceeds standard expectations.",
         {"code_correctness": 40, "react_loop_reasoning": 24, "error_handling": 18, "documentation": 10},
         92.0, "Outstanding work on typed tool schemas.", "published", 4),

        (3, 75.0, "Valid basic implementation. Note: 10% penalty applied due to submission after due date.",
         {"code_correctness": 32, "react_loop_reasoning": 18, "error_handling": 12, "documentation": 13},
         67.5, "Late penalty confirmed. Good baseline architecture.", "published", 4),

        (4, 85.0, "Strong architecture with StateGraph. Passes all automated test suites.",
         {"code_correctness": 36, "react_loop_reasoning": 21, "error_handling": 16, "documentation": 12},
         85.0, "Approved without modification.", "published", 4),

        (5, 83.0, "High cosine similarity (0.9626) detected matching Alex Chen's submission.",
         {"code_correctness": 38, "react_loop_reasoning": 22, "error_handling": 13, "documentation": 10},
         0.0, "Grade withheld: Plagiarism detected against alex_sub1.txt. Awaiting academic conduct interview.", "pending_approval", 4),

        # Vaish Student (ID 3, submission 6)
        (6, 94.0, "Flawless ReAct implementation. Thorough documentation and 100% test pass rate.",
         {"code_correctness": 39, "react_loop_reasoning": 25, "error_handling": 18, "documentation": 12},
         94.0, "Top tier submission in the cohort! Excellent work.", "published", 4),

        # Vaish on Assignment 2 (submission 7)
        (7, 90.0, "Clean 9-node StateGraph design with robust retry back-edge logic.",
         {"state_management": 28, "back_edge_retry": 28, "human_gate": 22, "testing": 12},
         90.0, "Faculty approved. Meets all production agent standards.", "published", 4),

        # Mike Student (ID 10, submission 9)
        (9, 81.0, "Good practical implementation with concise tool boundaries.",
         {"code_correctness": 34, "react_loop_reasoning": 20, "error_handling": 15, "documentation": 12},
         81.0, "Solid implementation.", "published", 4),
    ]

    for sub_id, dm, dfb, r_breakdown, fm, ffb, status, approver in grades_data:
        c.execute("SELECT id FROM grades WHERE submission_id = ?", (sub_id,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO grades (
                    submission_id, draft_marks, draft_feedback, draft_rubric_breakdown,
                    evidence_record, final_marks, final_feedback, status,
                    approved_by, approved_at, published_at, created_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, datetime('now', '-1 days'), datetime('now'), datetime('now', '-2 days')
                )
            """, (
                sub_id, dm, dfb, json.dumps(r_breakdown),
                json.dumps({"source": "AURAControlledRuntime", "verified": True}),
                fm, ffb, status, approver
            ))
    conn.commit()

    # -------------------------------------------------------------
    # 8. Project Groups across courses
    # -------------------------------------------------------------
    print("[8] Setting up project groups & student memberships...")
    groups = [
        # (group_id, course_id, name, desc)
        (1, 1, "Team Alpha: Autonomous Literature Agent", "End-to-end preprint research and evidence extraction pipeline."),
        (2, 1, "Team Beta: Automated Lab Grading Bot", "Self-healing LangGraph evaluator with human approval review node."),
        (3, 2, "Team Gamma: Distributed Swarm Crawler", "High-throughput parallel web indexing swarm with consensus merge."),
        (4, 3, "Team Delta: Safe Governance Gateway", "Deterministic safety filter and immutable cryptographic audit logger."),
    ]
    for gid, cid, name, desc in groups:
        c.execute("SELECT id FROM project_groups WHERE id = ?", (gid,))
        if not c.fetchone():
            c.execute("INSERT INTO project_groups (id, course_id, name, description, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                      (gid, cid, name, desc))
    conn.commit()

    # Group Memberships
    # Team Alpha (ID 1): Alex (5), Priya (6), Vaish Student (3)
    # Team Beta (ID 2): Marcus (7), Elena (8), David (9), Mike (10)
    # Team Gamma (ID 3): Vaish Student (3), Alex (5), Mike (10)
    # Team Delta (ID 4): Priya (6), Elena (8), Marcus (7)
    memberships = [
        (1, 5), (1, 6), (1, 3),
        (2, 7), (2, 8), (2, 9), (2, 10),
        (3, 3), (3, 5), (3, 10),
        (4, 6), (4, 8), (4, 7),
    ]
    for gid, sid in memberships:
        c.execute("SELECT id FROM group_members WHERE group_id = ? AND student_id = ?", (gid, sid))
        if not c.fetchone():
            c.execute("INSERT INTO group_members (group_id, student_id) VALUES (?, ?)", (gid, sid))
    conn.commit()

    # -------------------------------------------------------------
    # 9. Milestones & Milestone Progress for all groups
    # -------------------------------------------------------------
    print("[9] Populating milestones & progress trackers with health indicators...")
    milestones_specs = [
        # Course 1 (Dr. Vaishnavi Patel)
        (1, 1, "Checkpoint 1: Problem Statement & Literature Review", "Formal specification and initial survey paper.", datetime.utcnow() - timedelta(days=20), 1),
        (2, 1, "Checkpoint 2: Mid-term Prototype & MCP Connector", "Working code repository connected to FastMCP servers.", datetime.utcnow() + timedelta(days=7), 2),
        (3, 1, "Checkpoint 3: Final Demo, Validation & Capstone Report", "Production deployment, performance benchmarks, and presentation.", datetime.utcnow() + timedelta(days=28), 3),

        # Course 2 (Vaish)
        (4, 2, "Checkpoint 1: Architecture Blueprint & Node Schema", "Distributed topology design and state diagram.", datetime.utcnow() + timedelta(days=10), 1),
        (5, 2, "Checkpoint 2: Swarm Consensus & Benchmark Demo", "Parallel speedup verification under high load.", datetime.utcnow() + timedelta(days=30), 2),

        # Course 3 (Pooja)
        (6, 3, "Checkpoint 1: Threat Model & Audit Schema", "Definition of safety invariants and review node triggers.", datetime.utcnow() + timedelta(days=14), 1),
        (7, 3, "Checkpoint 2: Production Governance Sign-off", "End-to-end demo of halted execution on policy breach.", datetime.utcnow() + timedelta(days=35), 2),
    ]

    for mid, cid, title, desc, due, cp_num in milestones_specs:
        c.execute("SELECT id FROM milestones WHERE id = ?", (mid,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO milestones (id, course_id, title, description, due_date, checkpoint_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (mid, cid, title, desc, due.isoformat(), cp_num))
    conn.commit()

    # Milestone Progress:
    # (milestone_id, group_id, status, health, notes)
    progress_records = [
        # Course 1 - Team Alpha (Group 1)
        (1, 1, "approved", "green", "Checkpoint 1 approved by Dr. Patel. Excellent literature synthesis."),
        (2, 1, "in_progress", "green", "MCP connector implemented and verified against local notes store."),
        (3, 1, "not_started", "green", "Final demo scheduled for Week 14."),

        # Course 1 - Team Beta (Group 2)
        (1, 2, "approved", "green", "Approved with minor feedback on similarity metrics."),
        (2, 2, "submitted", "amber", "Prototype submitted; pending benchmark tuning."),
        (3, 2, "not_started", "amber", "Drafting capstone presentation."),

        # Course 2 - Team Gamma (Group 3)
        (4, 3, "in_progress", "green", "Swarm coordinator topology finalized."),
        (5, 3, "not_started", "green", "Consensus benchmark test harness in preparation."),

        # Course 3 - Team Delta (Group 4)
        (6, 4, "in_progress", "green", "Audit database schema and gate policies drafted."),
        (7, 4, "not_started", "green", "Awaiting checkpoint 1 completion."),
    ]

    for mid, gid, status, health, notes in progress_records:
        c.execute("SELECT id FROM milestone_progress WHERE milestone_id = ? AND group_id = ?", (mid, gid))
        row = c.fetchone()
        if not row:
            c.execute("""
                INSERT INTO milestone_progress (milestone_id, group_id, status, health, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (mid, gid, status, health, notes))
        else:
            c.execute("""
                UPDATE milestone_progress SET status = ?, health = ?, notes = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (status, health, notes, row[0]))
    conn.commit()

    conn.close()
    print("\n[SUCCESS] Comprehensive dummy data populated successfully across all accounts!")

if __name__ == "__main__":
    populate_all()
