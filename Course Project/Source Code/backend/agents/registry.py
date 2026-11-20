"""
AURA Production Seven-Agent System Registry.
Formal consolidation conforming to prompt.md Section 3:
  1. AURA Orchestrator (Supervisor & StateGraph Coordinator)
  2. Notes & Knowledge Agent (Document Processing, Versioning & Semantic RAG)
  3. Assignment & Distribution Agent (Rubrics, Distribution & Deadlines)
  4. Submission & Collection Agent (Idempotent Intake, Validation & Integrity)
  5. Similarity & Academic Integrity Agent (Hybrid Plagiarism & Evidence Matching)
  6. Grading & Feedback Agent (Gemini Reasoning & Criterion-wise Draft Marks)
  7. Project & Milestone Agent (Group Tracking, Deliverables & Checkpoints)
"""
from typing import Dict, Any, List

SEVEN_CORE_AGENTS: List[Dict[str, Any]] = [
    {
        "agent_id": 1,
        "name": "AURAOrchestrator",
        "display_name": "AURA Orchestrator & Supervisor",
        "role": "Central coordinator and supervisor",
        "responsibilities": [
            "Understand user academic requests",
            "Identify course and relevant context",
            "Determine specialist agent routing",
            "Maintain shared LangGraph workflow state",
            "Handle retries and execution checkpoints",
            "Enforce faculty approval before publication",
        ],
        "module": "agents.coordinator.AURACoordinator",
        "runtime_type": "LangGraph Supervisor",
        "governed": True,
    },
    {
        "agent_id": 2,
        "name": "NotesKnowledgeAgent",
        "display_name": "Notes & Knowledge Agent",
        "role": "Document ingestion, versioning and semantic retrieval",
        "responsibilities": [
            "Upload and organize course notes",
            "Extract PDF, DOCX and text content",
            "Organize notes by unit, chapter and topic",
            "Maintain document version ancestry (parent-child)",
            "Generate embeddings via pgvector / Gemini",
            "Perform course-aware semantic retrieval with citations",
        ],
        "module": "agents.notes_repository.NotesRepositoryAgent",
        "runtime_type": "Deterministic RAG Service",
        "governed": True,
    },
    {
        "agent_id": 3,
        "name": "AssignmentDistributionAgent",
        "display_name": "Assignment & Distribution Agent",
        "role": "Assignment creation, rubric validation and release",
        "responsibilities": [
            "Create structured assignment descriptions",
            "Generate and validate rubric criteria totals",
            "Enforce faculty approval before publication",
            "Manage release schedules and deadline reminders",
            "Maintain assignment version lineage",
        ],
        "module": "agents.assignment_distribution.AssignmentDistributionAgent",
        "runtime_type": "Deterministic Publishing Service",
        "governed": True,
    },
    {
        "agent_id": 4,
        "name": "SubmissionCollectionAgent",
        "display_name": "Submission & Collection Agent",
        "role": "Intake, file integrity, timestamping and idempotency",
        "responsibilities": [
            "Receive student submissions",
            "Validate file format, size and checksums",
            "Record authoritative server-side timestamps",
            "Determine late vs on-time delta",
            "Preserve original files securely in storage",
            "Extract text for downstream agent analysis",
        ],
        "module": "agents.submission_collection.SubmissionCollectionAgent",
        "runtime_type": "Deterministic Storage Agent",
        "governed": True,
    },
    {
        "agent_id": 5,
        "name": "SimilarityIntegrityAgent",
        "display_name": "Similarity & Academic Integrity Agent",
        "role": "Plagiarism analysis and evidence detection",
        "responsibilities": [
            "Pairwise TF-IDF and cosine similarity calculation",
            "Detect copied passages and code overlap",
            "Flag matching submissions with traceable evidence",
            "Enforce critical guardrail: flags for faculty review only",
            "Never automatically punish or assign misconduct",
        ],
        "module": "agents.plagiarism_similarity.PlagiarismSimilarityAgent",
        "runtime_type": "Hybrid TF-IDF / Embedding Engine",
        "governed": True,
    },
    {
        "agent_id": 6,
        "name": "GradingFeedbackAgent",
        "display_name": "Grading & Feedback Agent",
        "role": "AI-assisted criterion evaluation and feedback drafting",
        "responsibilities": [
            "Retrieve rubric and original student submission",
            "Evaluate work against each rubric criterion via Gemini",
            "Produce criterion-wise draft marks with supporting evidence",
            "Generate personalized feedback and missing requirement notes",
            "Deterministic validation of rubric totals and numeric ranges",
            "Enforce critical guardrail: draft marks only, requires faculty approval",
        ],
        "module": "agents.grading_assistance.GradingAssistanceAgent",
        "runtime_type": "Gemini Structured Output Agent",
        "governed": True,
    },
    {
        "agent_id": 7,
        "name": "ProjectMilestoneAgent",
        "display_name": "Project & Milestone Agent",
        "role": "Student project groups, milestones and progress tracking",
        "responsibilities": [
            "Track project team groups and memberships",
            "Monitor milestones against due dates",
            "Receive milestone deliverables and GitHub links",
            "Compute milestone health (green/amber/red)",
            "Summarize team progress and identify delayed checkpoints",
        ],
        "module": "agents.project_milestone.ProjectMilestoneAgent",
        "runtime_type": "Hybrid Deterministic / LLM Agent",
        "governed": True,
    },
]


class AgentRegistry:
    @staticmethod
    def get_all_agents() -> List[Dict[str, Any]]:
        return SEVEN_CORE_AGENTS

    @staticmethod
    def get_agent_by_id(agent_id: int) -> Dict[str, Any]:
        for a in SEVEN_CORE_AGENTS:
            if a["agent_id"] == agent_id:
                return a
        raise KeyError(f"Agent with ID {agent_id} not registered")

    @staticmethod
    def get_agent_by_name(name: str) -> Dict[str, Any]:
        for a in SEVEN_CORE_AGENTS:
            if a["name"].lower() == name.lower():
                return a
        raise KeyError(f"Agent '{name}' not registered")
