from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime
import enum
from config import settings


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    faculty = "faculty"
    student = "student"
    hod = "hod"


class AssignmentStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class GradeStatus(str, enum.Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    published = "published"


class MilestoneHealth(str, enum.Enum):
    green = "green"
    amber = "amber"
    red = "red"


class MilestoneProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    submitted = "submitted"
    approved = "approved"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.student)
    created_at = Column(DateTime, default=datetime.utcnow)

    courses_taught = relationship("Course", back_populates="faculty")
    enrollments = relationship("CourseEnrollment", back_populates="student")
    notes_uploaded = relationship("Note", back_populates="uploader")
    submissions = relationship("Submission", back_populates="student")
    grades_approved = relationship("Grade", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="actor")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, default="")
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("User", back_populates="courses_taught")
    enrollments = relationship("CourseEnrollment", back_populates="course")
    notes = relationship("Note", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    milestones = relationship("Milestone", back_populates="course")
    project_groups = relationship("ProjectGroup", back_populates="course")
    lesson_plan = relationship("LessonPlan", back_populates="course", uselist=False, cascade="all, delete-orphan")
    units = relationship("CourseUnit", back_populates="course", order_by="CourseUnit.unit_number", cascade="all, delete-orphan")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(300), nullable=False)
    unit = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(300), nullable=False)
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("course_chapters.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="notes")
    uploader = relationship("User", back_populates="notes_uploaded")
    chapter = relationship("CourseChapter", back_populates="notes")
    lesson = relationship("CourseLesson", back_populates="notes")
    versions = relationship("Note", foreign_keys=[parent_id])


class LessonPlan(Base):
    __tablename__ = "lesson_plans"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), unique=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(300), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="lesson_plan")
    uploader = relationship("User")


class CourseUnit(Base):
    __tablename__ = "course_units"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)

    course = relationship("Course", back_populates="units")
    chapters = relationship("CourseChapter", back_populates="unit", order_by="CourseChapter.chapter_number", cascade="all, delete-orphan")


class CourseChapter(Base):
    __tablename__ = "course_chapters"
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("course_units.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)

    unit = relationship("CourseUnit", back_populates="chapters")
    topics = relationship("CourseTopic", back_populates="chapter", order_by="CourseTopic.topic_number", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="chapter", order_by="Note.created_at", cascade="all, delete-orphan")
    lessons = relationship("CourseLesson", back_populates="chapter", order_by="CourseLesson.lesson_number", cascade="all, delete-orphan")


class CourseTopic(Base):
    __tablename__ = "course_topics"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("course_chapters.id"), nullable=False)
    topic_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)

    chapter = relationship("CourseChapter", back_populates="topics")


class CourseLesson(Base):
    __tablename__ = "course_lessons"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("course_chapters.id"), nullable=False)
    lesson_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)

    chapter = relationship("CourseChapter", back_populates="lessons")
    notes = relationship("Note", back_populates="lesson")


class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    rubric = Column(Text, nullable=False)  # JSON string
    max_marks = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default=AssignmentStatus.draft)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(300), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_late = Column(Boolean, default=False)
    similarity_score = Column(Float, nullable=True)
    similarity_flags = Column(Text, nullable=True)  # JSON string
    status = Column(String(20), default="submitted")

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    grade = relationship("Grade", back_populates="submission", uselist=False)


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    draft_marks = Column(Float, nullable=True)
    draft_feedback = Column(Text, nullable=True)
    draft_rubric_breakdown = Column(Text, nullable=True)  # JSON
    evidence_record = Column(Text, nullable=True)  # JSON
    final_marks = Column(Float, nullable=True)
    final_feedback = Column(Text, nullable=True)
    status = Column(String(25), default=GradeStatus.draft)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submission = relationship("Submission", back_populates="grade")
    approver = relationship("User", back_populates="grades_approved")


class ProjectGroup(Base):
    __tablename__ = "project_groups"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    github_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="project_groups")
    members = relationship("GroupMember", back_populates="group")
    milestone_progress = relationship("MilestoneProgress", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("project_groups.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    group = relationship("ProjectGroup", back_populates="members")


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    due_date = Column(DateTime, nullable=False)
    checkpoint_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="milestones")
    progress = relationship("MilestoneProgress", back_populates="milestone")


class MilestoneProgress(Base):
    __tablename__ = "milestone_progress"
    id = Column(Integer, primary_key=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("project_groups.id"), nullable=False)
    status = Column(String(20), default=MilestoneProgressStatus.not_started)
    submission_file = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    health = Column(String(10), default=MilestoneHealth.green)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    milestone = relationship("Milestone", back_populates="progress")
    group = relationship("ProjectGroup", back_populates="milestone_progress")


class ProjectFeedback(Base):
    __tablename__ = "project_feedback"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("project_groups.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)  # Checkpoint ID, or None for team-level GitHub feedback
    category = Column(String(30), nullable=False, default="checkpoint")  # "checkpoint" or "github"
    feedback_text = Column(Text, nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course")
    group = relationship("ProjectGroup")
    milestone = relationship("Milestone")
    faculty = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    input_data = Column(Text, nullable=True)   # JSON
    output_data = Column(Text, nullable=True)  # JSON
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    actor = relationship("User", back_populates="audit_logs")


class RunContext(Base):
    __tablename__ = "run_contexts"
    id = Column(Integer, primary_key=True)
    run_id = Column(String(64), unique=True, nullable=False)
    status = Column(String(20), default="running")  # running, completed, failed, escalated
    plan = Column(Text, nullable=True)       # JSON
    state = Column(Text, nullable=True)      # JSON
    version = Column(Integer, default=1)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class DocumentChunk(Base):
    """Semantic vector chunks for lecture notes. Supports persistent embedding retrieval."""
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    embedding_model = Column(String(100), nullable=False, default="models/text-embedding-004")
    embedding_json = Column(Text, nullable=True)  # JSON-encoded float array for cross-platform DB compatibility
    access_scope = Column(String(50), default="course")
    created_at = Column(DateTime, default=datetime.utcnow)

    note = relationship("Note")
    course = relationship("Course")


class FacultyApprovalRecord(Base):
    """Immutable audit trail for every human faculty review & grade publishing decision."""
    __tablename__ = "faculty_approval_records"
    id = Column(Integer, primary_key=True)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)  # submitted, approved, rejected, published, rollback
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    marks_before = Column(Float, nullable=True)
    marks_after = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    grade = relationship("Grade")
    faculty = relationship("User")


class WorkflowThread(Base):
    """LangGraph production workflow thread and checkpoint persistence."""
    __tablename__ = "workflow_threads"
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(64), unique=True, nullable=False, index=True)
    run_id = Column(String(64), nullable=True)
    agent_name = Column(String(100), nullable=False)
    current_node = Column(String(100), nullable=True)
    workflow_status = Column(String(30), default="running")  # running, waiting_approval, completed, failed
    state_json = Column(Text, nullable=True)
    approval_status = Column(String(30), nullable=True)
    error_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class AgentMetrics(Base):
    """Observability telemetry for agent execution latencies, token consumption and tool errors."""
    __tablename__ = "agent_metrics"
    id = Column(Integer, primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    llm_latency_ms = Column(Float, nullable=True)
    token_input = Column(Integer, nullable=True)
    token_output = Column(Integer, nullable=True)
    mcp_tool_name = Column(String(100), nullable=True)
    mcp_latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
