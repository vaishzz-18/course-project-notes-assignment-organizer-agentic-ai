"""
Seed script: populates the database with realistic dummy data for demo purposes.
Course: CS401 — Agentic AI & Autonomous Systems
Faculty: Dr. Vaishnavi Patel (faculty@aura.edu / faculty123)
Students: Alex Chen, Priya Sharma, Marcus Vance, Elena Rostova, David Kim (student123)
Includes: Notes with versions, Assignment with 100-mark rubric, Submissions (late + duplicate for plagiarism), and Milestone checkpoints.
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from models.database import (
    Base, engine, AsyncSessionLocal, User, UserRole, Course, CourseEnrollment,
    Note, Assignment, AssignmentStatus, Submission, Grade, GradeStatus,
    ProjectGroup, GroupMember, Milestone, MilestoneProgress, MilestoneProgressStatus, MilestoneHealth
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    print("Initializing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        res = await session.execute(select(Course).where(Course.code == "CS401"))
        if res.scalar_one_or_none():
            print("CS401 is already seeded in database.")
            return

        print("Seeding Users...")
        faculty = User(
            name="Dr. Vaishnavi Patel",
            email="faculty@aura.edu",
            password_hash=pwd_context.hash("faculty123"),
            role=UserRole.faculty
        )
        s1 = User(name="Alex Chen", email="alex@aura.edu", password_hash=pwd_context.hash("student123"), role=UserRole.student)
        s2 = User(name="Priya Sharma", email="priya@aura.edu", password_hash=pwd_context.hash("student123"), role=UserRole.student)
        s3 = User(name="Marcus Vance", email="marcus@aura.edu", password_hash=pwd_context.hash("student123"), role=UserRole.student)
        s4 = User(name="Elena Rostova", email="elena@aura.edu", password_hash=pwd_context.hash("student123"), role=UserRole.student)
        s5 = User(name="David Kim", email="david@aura.edu", password_hash=pwd_context.hash("student123"), role=UserRole.student)

        session.add_all([faculty, s1, s2, s3, s4, s5])
        await session.flush()

        print("Seeding Course CS401...")
        course = Course(
            name="Agentic AI & Autonomous Systems",
            code="CS401",
            description="Comprehensive course covering ReAct loops, MCP connectors, LangGraph orchestration, and multi-agent swarms.",
            faculty_id=faculty.id
        )
        session.add(course)
        await session.flush()

        for s in [s1, s2, s3, s4, s5]:
            session.add(CourseEnrollment(course_id=course.id, student_id=s.id))

        print("Seeding Notes Repository with Versioning...")
        notes_dir = Path(__file__).parent.parent / "data" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        f1_v1 = notes_dir / "unit1_foundations_v1.txt"
        f1_v1.write_text("Unit 1: Agentic Foundations (v1)\nAgent definition: Perception, Reasoning, Action loop. Agent vs Chatbot distinction.")
        n1_v1 = Note(
            course_id=course.id,
            title="Lecture 1: Foundations of Agentic AI",
            unit="Unit 1",
            topic="Agent Architecture",
            file_path=str(f1_v1),
            file_name="unit1_foundations_v1.txt",
            version=1,
            is_current=False,
            uploaded_by=faculty.id
        )
        session.add(n1_v1)
        await session.flush()

        f1_v2 = notes_dir / "unit1_foundations_v2.txt"
        f1_v2.write_text("Unit 1: Agentic Foundations (v2 Updated)\nExpanded coverage on ReAct cognitive cycles, prompt decomposition, and stopping conditions.")
        n1_v2 = Note(
            course_id=course.id,
            title="Lecture 1: Foundations of Agentic AI (v2)",
            unit="Unit 1",
            topic="Agent Architecture",
            file_path=str(f1_v2),
            file_name="unit1_foundations_v2.txt",
            version=2,
            is_current=True,
            parent_id=n1_v1.id,
            uploaded_by=faculty.id
        )

        f2 = notes_dir / "unit2_mcp_tools.txt"
        f2.write_text("Unit 2: Tools & Model Context Protocol (MCP)\nDecoupling data access from agent logic using standard JSON-RPC MCP servers.")
        n2 = Note(
            course_id=course.id,
            title="Lecture 2: MCP & Typed Tool Execution",
            unit="Unit 2",
            topic="MCP Protocol",
            file_path=str(f2),
            file_name="unit2_mcp_tools.txt",
            version=1,
            is_current=True,
            uploaded_by=faculty.id
        )

        f3 = notes_dir / "unit3_langgraph.txt"
        f3.write_text("Unit 3: LangGraph StateGraphs\nState management, conditional routing, human-in-the-loop review nodes, and retry back-edges.")
        n3 = Note(
            course_id=course.id,
            title="Lecture 3: LangGraph Orchestration",
            unit="Unit 3",
            topic="State Graphs",
            file_path=str(f3),
            file_name="unit3_langgraph.txt",
            version=1,
            is_current=True,
            uploaded_by=faculty.id
        )

        session.add_all([n1_v2, n2, n3])
        await session.flush()

        print("Seeding Assignment with 100-mark Rubric...")
        rubric = {
            "code_correctness": {"max": 40, "description": "Correct tool invocation and valid output generation"},
            "react_loop_reasoning": {"max": 25, "description": "Clear thought-action-observation trace in logs"},
            "error_handling": {"max": 20, "description": "Graceful recovery when a tool fails or inputs are malformed"},
            "documentation": {"max": 15, "description": "Code comments, architecture diagram, and README instructions"}
        }
        due = datetime.utcnow() + timedelta(days=7)
        assign = Assignment(
            course_id=course.id,
            title="Assignment 1: Build a Tool-Using ReAct Agent",
            description="Design and implement an autonomous ReAct agent with at least 3 typed tools and bounded retry logic.",
            rubric=json.dumps(rubric),
            max_marks=100.0,
            due_date=due,
            status=AssignmentStatus.published,
            created_by=faculty.id,
            published_at=datetime.utcnow() - timedelta(days=2)
        )
        session.add(assign)
        await session.flush()

        print("Seeding Submissions (including late and high similarity cases)...")
        sub_dir = Path(__file__).parent.parent / "data" / "submissions"
        sub_dir.mkdir(parents=True, exist_ok=True)

        # 1. Alex Chen (On time, high quality)
        f_alex = sub_dir / "alex_sub1.txt"
        alex_text = '''# ReAct Agent Implementation by Alex Chen
import json

class ReActAgent:
    def __init__(self, tools):
        self.tools = tools
        self.memory = []

    def reason_and_act(self, query):
        print(f"Thought: Analyzing query '{query}'")
        for tool in self.tools:
            if tool.can_handle(query):
                res = tool.execute(query)
                return f"Final Answer: {res}"
        return "Cannot solve query"
'''
        f_alex.write_text(alex_text)
        sub_alex = Submission(
            assignment_id=assign.id,
            student_id=s1.id,
            file_path=str(f_alex),
            file_name="alex_sub1.txt",
            submitted_at=datetime.utcnow() - timedelta(days=1),
            is_late=False,
            similarity_score=0.12,
            status="submitted"
        )

        # 2. Priya Sharma (On time, good quality)
        f_priya = sub_dir / "priya_sub1.txt"
        priya_text = '''# ReAct Tool Agent by Priya Sharma
from typing import Dict, Any

class AgentPipeline:
    def __init__(self):
        self.log = []

    def execute_react_step(self, user_prompt: str) -> Dict[str, Any]:
        # Thought: Check data connector
        # Action: Query notes
        return {"status": "success", "result": "Calculated accurately with tools"}
'''
        f_priya.write_text(priya_text)
        sub_priya = Submission(
            assignment_id=assign.id,
            student_id=s2.id,
            file_path=str(f_priya),
            file_name="priya_sub1.txt",
            submitted_at=datetime.utcnow() - timedelta(days=2),
            is_late=False,
            similarity_score=0.15,
            status="submitted"
        )

        # 3. Marcus Vance (Late submission)
        f_marcus = sub_dir / "marcus_sub1.txt"
        f_marcus.write_text('# ReAct implementation Marcus Vance\ndef solve(): return "done"')
        sub_marcus = Submission(
            assignment_id=assign.id,
            student_id=s3.id,
            file_path=str(f_marcus),
            file_name="marcus_sub1.txt",
            submitted_at=datetime.utcnow() + timedelta(days=8),
            is_late=True,
            similarity_score=0.08,
            status="submitted"
        )

        # 4. Elena Rostova (On time)
        f_elena = sub_dir / "elena_sub1.txt"
        f_elena.write_text("# Elena Rostova - StateGraph ReAct\n# Uses typed tools and schema validation.")
        sub_elena = Submission(
            assignment_id=assign.id,
            student_id=s4.id,
            file_path=str(f_elena),
            file_name="elena_sub1.txt",
            submitted_at=datetime.utcnow() - timedelta(hours=12),
            is_late=False,
            similarity_score=0.18,
            status="submitted"
        )

        # 5. David Kim (High similarity to Alex - tests plagiarism!)
        f_david = sub_dir / "david_sub1.txt"
        f_david.write_text(alex_text.replace("Alex Chen", "David Kim"))
        sub_david = Submission(
            assignment_id=assign.id,
            student_id=s5.id,
            file_path=str(f_david),
            file_name="david_sub1.txt",
            submitted_at=datetime.utcnow() - timedelta(hours=6),
            is_late=False,
            similarity_score=0.96,
            similarity_flags=json.dumps([{"with_student": "Alex Chen", "score": 0.96, "reason": "Identical code body"}]),
            status="submitted"
        )

        session.add_all([sub_alex, sub_priya, sub_marcus, sub_elena, sub_david])
        await session.flush()

        print("Seeding Project Groups & Milestones...")
        g1 = ProjectGroup(
            course_id=course.id,
            name="Team Alpha: Autonomous Literature Agent",
            description="An autonomous agent for searching, analyzing, and synthesizing scientific papers."
        )
        g2 = ProjectGroup(
            course_id=course.id,
            name="Team Beta: Automated Lab Grading Bot",
            description="A multi-agent swarm for evaluating coding lab exams with test runners."
        )
        session.add_all([g1, g2])
        await session.flush()

        session.add_all([
            GroupMember(group_id=g1.id, student_id=s1.id),
            GroupMember(group_id=g1.id, student_id=s2.id),
            GroupMember(group_id=g2.id, student_id=s3.id),
            GroupMember(group_id=g2.id, student_id=s4.id),
            GroupMember(group_id=g2.id, student_id=s5.id),
        ])

        m1 = Milestone(
            course_id=course.id,
            title="Checkpoint 1: Problem Statement & Literature Review",
            checkpoint_number=1,
            due_date=datetime.utcnow() - timedelta(days=5)
        )
        m2 = Milestone(
            course_id=course.id,
            title="Checkpoint 2: Mid-term Prototype & MCP Connector",
            checkpoint_number=2,
            due_date=datetime.utcnow() + timedelta(days=10)
        )
        m3 = Milestone(
            course_id=course.id,
            title="Checkpoint 3: Final Demo, Validation & Capstone Report",
            checkpoint_number=3,
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        session.add_all([m1, m2, m3])
        await session.flush()

        p1_g1 = MilestoneProgress(
            milestone_id=m1.id, group_id=g1.id, status=MilestoneProgressStatus.approved,
            health=MilestoneHealth.green, notes="Approved by faculty with distinction."
        )
        p2_g1 = MilestoneProgress(
            milestone_id=m2.id, group_id=g1.id, status=MilestoneProgressStatus.in_progress,
            health=MilestoneHealth.green, notes="On track. MCP tools implemented."
        )
        p1_g2 = MilestoneProgress(
            milestone_id=m1.id, group_id=g2.id, status=MilestoneProgressStatus.submitted,
            health=MilestoneHealth.green, notes="Submitted for faculty review."
        )
        p2_g2 = MilestoneProgress(
            milestone_id=m2.id, group_id=g2.id, status=MilestoneProgressStatus.not_started,
            health=MilestoneHealth.amber, notes="Needs attention; behind schedule."
        )
        session.add_all([p1_g1, p2_g1, p1_g2, p2_g2])

        await session.commit()
        print("Database successfully seeded with realistic dummy course data!")


if __name__ == "__main__":
    asyncio.run(seed())
