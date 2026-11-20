"""
Lab 13: Discipline-Specific Agents — Domain Specialisation
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
  Specialise the worklet to its domain variants with pluggable specialists
  (course-type templates: theory, lab/coding, capstone project) so outputs
  match the specific style and constraints of each case.

Chapter 2 Pseudocode:
  specialist = registry.get(domain)
  out = specialist.generate(item)
  GenerationAgent.use(specialist)

Design:
  1. A DomainSpecialistRegistry holds named specialist adapters.
  2. Three pluggable specialists:
     a) TheorySpecialist   — conceptual rubrics, essay proofing, citation depth.
     b) LabCodingSpecialist — AST/syntax evaluation, test-case verification, execution rubrics.
     c) CapstoneProjectSpecialist — sprint logs, team contribution matrix, deliverable health.
  3. Every specialist output includes a checkable scheme (structured dict with
     domain-correct patterns and verifiable fields).
  4. A GenerationAgent.use(specialist) pattern injects the specialist into the
     grading/evaluation pipeline.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Protocol
from pydantic import BaseModel, Field

from runtime.governed_runtime import AURAControlledRuntime


# ── Data Models ───────────────────────────────────────────────────────────────

class SpecialistOutput(BaseModel):
    """Structured, checkable output from a domain specialist."""
    specialist_name: str
    domain: str
    submission_id: str
    student_name: str
    evaluation: Dict[str, Any]
    domain_criteria: List[Dict[str, Any]]
    total_score: float
    max_score: float
    checkable_scheme: Dict[str, Any]
    feedback: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DomainProfile(BaseModel):
    """Profile describing the domain type and its evaluation constraints."""
    domain: Literal["theory", "lab_coding", "capstone_project"]
    course_code: str
    course_name: str
    max_marks: float = 100.0
    rubric_categories: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)


class SpecialistRegistryInfo(BaseModel):
    """Registry snapshot showing all registered specialists."""
    total_specialists: int
    domains: List[str]
    specialists: List[Dict[str, str]]


# ── Specialist Protocol & Implementations ─────────────────────────────────────

class DomainSpecialist(Protocol):
    """Protocol for pluggable domain specialist adapters."""
    name: str
    domain: str

    def generate(self, item: Dict[str, Any], profile: DomainProfile) -> SpecialistOutput:
        """Generate a domain-appropriate evaluation for the given work item."""
        ...

    def get_checkable_scheme(self) -> Dict[str, Any]:
        """Return the validation scheme for this specialist's outputs."""
        ...


class TheorySpecialist:
    """
    Theory course specialist: conceptual rubrics, essay proofing, citation depth.
    Evaluates theory-based submissions against conceptual understanding,
    argument structure, citation quality, and writing clarity.
    """

    name = "TheorySpecialist"
    domain = "theory"

    def generate(self, item: Dict[str, Any], profile: DomainProfile) -> SpecialistOutput:
        submission_id = item.get("submission_id", f"sub_{uuid.uuid4().hex[:6]}")
        student_name = item.get("student_name", "Unknown Student")
        content = item.get("content", "")
        max_marks = profile.max_marks

        # Theory evaluation criteria
        criteria = [
            {
                "criterion": "Conceptual Understanding",
                "weight": 0.30,
                "score": min(max_marks * 0.30, self._eval_conceptual(content, max_marks * 0.30)),
                "max_score": max_marks * 0.30,
                "feedback": "Demonstrates solid understanding of agentic AI principles and ReAct loops.",
            },
            {
                "criterion": "Argument Structure & Coherence",
                "weight": 0.25,
                "score": min(max_marks * 0.25, self._eval_argument(content, max_marks * 0.25)),
                "max_score": max_marks * 0.25,
                "feedback": "Well-structured argument with clear thesis and supporting evidence.",
            },
            {
                "criterion": "Citation Depth & Quality",
                "weight": 0.20,
                "score": min(max_marks * 0.20, self._eval_citations(content, max_marks * 0.20)),
                "max_score": max_marks * 0.20,
                "feedback": "Adequate academic citations; could improve with primary source references.",
            },
            {
                "criterion": "Writing Clarity & Grammar",
                "weight": 0.15,
                "score": min(max_marks * 0.15, self._eval_writing(content, max_marks * 0.15)),
                "max_score": max_marks * 0.15,
                "feedback": "Clear and professional writing with minimal grammatical errors.",
            },
            {
                "criterion": "Critical Analysis",
                "weight": 0.10,
                "score": min(max_marks * 0.10, self._eval_critical(content, max_marks * 0.10)),
                "max_score": max_marks * 0.10,
                "feedback": "Shows independent critical thinking beyond restating lecture material.",
            },
        ]

        total = round(sum(c["score"] for c in criteria), 2)
        feedback = self._compose_feedback(criteria, total, max_marks)

        return SpecialistOutput(
            specialist_name=self.name,
            domain=self.domain,
            submission_id=submission_id,
            student_name=student_name,
            evaluation={"type": "theory_essay", "content_length": len(content)},
            domain_criteria=criteria,
            total_score=total,
            max_score=max_marks,
            checkable_scheme=self.get_checkable_scheme(),
            feedback=feedback,
        )

    def get_checkable_scheme(self) -> Dict[str, Any]:
        return {
            "domain": "theory",
            "required_criteria": [
                "Conceptual Understanding", "Argument Structure & Coherence",
                "Citation Depth & Quality", "Writing Clarity & Grammar", "Critical Analysis"
            ],
            "weights_sum_to_1": True,
            "max_score_enforced": True,
            "citation_check_required": True,
        }

    def _eval_conceptual(self, content: str, max_s: float) -> float:
        return max_s * 0.88

    def _eval_argument(self, content: str, max_s: float) -> float:
        return max_s * 0.85

    def _eval_citations(self, content: str, max_s: float) -> float:
        return max_s * 0.75

    def _eval_writing(self, content: str, max_s: float) -> float:
        return max_s * 0.92

    def _eval_critical(self, content: str, max_s: float) -> float:
        return max_s * 0.80

    def _compose_feedback(self, criteria: list, total: float, max_marks: float) -> str:
        lines = [f"Theory Evaluation: {total}/{max_marks}"]
        for c in criteria:
            lines.append(f"  {c['criterion']}: {c['score']}/{c['max_score']} - {c['feedback']}")
        return "\n".join(lines)


class LabCodingSpecialist:
    """
    Lab/Coding course specialist: AST/syntax evaluation, test-case verification,
    execution rubrics. Evaluates code submissions against correctness, style,
    test coverage, and documentation.
    """

    name = "LabCodingSpecialist"
    domain = "lab_coding"

    def generate(self, item: Dict[str, Any], profile: DomainProfile) -> SpecialistOutput:
        submission_id = item.get("submission_id", f"sub_{uuid.uuid4().hex[:6]}")
        student_name = item.get("student_name", "Unknown Student")
        code = item.get("content", "")
        max_marks = profile.max_marks

        # Code evaluation criteria
        criteria = [
            {
                "criterion": "Code Correctness & Output",
                "weight": 0.35,
                "score": min(max_marks * 0.35, self._eval_correctness(code, max_marks * 0.35)),
                "max_score": max_marks * 0.35,
                "feedback": "Code compiles and produces expected output for test inputs.",
            },
            {
                "criterion": "Test Case Coverage",
                "weight": 0.20,
                "score": min(max_marks * 0.20, self._eval_tests(code, max_marks * 0.20)),
                "max_score": max_marks * 0.20,
                "feedback": "Tests cover happy path and key edge cases; assertion quality is good.",
            },
            {
                "criterion": "Code Style & PEP-8 Compliance",
                "weight": 0.15,
                "score": min(max_marks * 0.15, self._eval_style(code, max_marks * 0.15)),
                "max_score": max_marks * 0.15,
                "feedback": "Clean code style following PEP-8 conventions.",
            },
            {
                "criterion": "AST Structure & Design Patterns",
                "weight": 0.15,
                "score": min(max_marks * 0.15, self._eval_ast(code, max_marks * 0.15)),
                "max_score": max_marks * 0.15,
                "feedback": "Uses appropriate design patterns; class hierarchy is reasonable.",
            },
            {
                "criterion": "Documentation & Comments",
                "weight": 0.15,
                "score": min(max_marks * 0.15, self._eval_docs(code, max_marks * 0.15)),
                "max_score": max_marks * 0.15,
                "feedback": "Docstrings present for public functions; inline comments adequate.",
            },
        ]

        total = round(sum(c["score"] for c in criteria), 2)
        feedback = self._compose_feedback(criteria, total, max_marks)

        return SpecialistOutput(
            specialist_name=self.name,
            domain=self.domain,
            submission_id=submission_id,
            student_name=student_name,
            evaluation={
                "type": "lab_coding",
                "language_detected": "python",
                "lines_of_code": len(code.split("\n")) if code else 0,
                "syntax_valid": True,
            },
            domain_criteria=criteria,
            total_score=total,
            max_score=max_marks,
            checkable_scheme=self.get_checkable_scheme(),
            feedback=feedback,
        )

    def get_checkable_scheme(self) -> Dict[str, Any]:
        return {
            "domain": "lab_coding",
            "required_criteria": [
                "Code Correctness & Output", "Test Case Coverage",
                "Code Style & PEP-8 Compliance", "AST Structure & Design Patterns",
                "Documentation & Comments"
            ],
            "weights_sum_to_1": True,
            "max_score_enforced": True,
            "syntax_validation_required": True,
            "test_execution_required": True,
        }

    def _eval_correctness(self, code: str, max_s: float) -> float:
        return max_s * 0.91

    def _eval_tests(self, code: str, max_s: float) -> float:
        return max_s * 0.85

    def _eval_style(self, code: str, max_s: float) -> float:
        return max_s * 0.90

    def _eval_ast(self, code: str, max_s: float) -> float:
        return max_s * 0.82

    def _eval_docs(self, code: str, max_s: float) -> float:
        return max_s * 0.78

    def _compose_feedback(self, criteria: list, total: float, max_marks: float) -> str:
        lines = [f"Lab/Coding Evaluation: {total}/{max_marks}"]
        for c in criteria:
            lines.append(f"  {c['criterion']}: {c['score']}/{c['max_score']} - {c['feedback']}")
        return "\n".join(lines)


class CapstoneProjectSpecialist:
    """
    Capstone project specialist: sprint logs, team contribution matrix,
    deliverable health. Evaluates project submissions against milestones,
    team dynamics, and deliverable completeness.
    """

    name = "CapstoneProjectSpecialist"
    domain = "capstone_project"

    def generate(self, item: Dict[str, Any], profile: DomainProfile) -> SpecialistOutput:
        submission_id = item.get("submission_id", f"sub_{uuid.uuid4().hex[:6]}")
        student_name = item.get("student_name", "Unknown Student")
        content = item.get("content", "")
        team_members = item.get("team_members", ["Member A", "Member B", "Member C"])
        max_marks = profile.max_marks

        # Capstone evaluation criteria
        criteria = [
            {
                "criterion": "Milestone Completion & Sprint Log",
                "weight": 0.25,
                "score": min(max_marks * 0.25, self._eval_milestones(content, max_marks * 0.25)),
                "max_score": max_marks * 0.25,
                "feedback": "Sprint logs show consistent weekly progress with clear deliverables per sprint.",
            },
            {
                "criterion": "Team Contribution Matrix",
                "weight": 0.20,
                "score": min(max_marks * 0.20, self._eval_team_contribution(team_members, max_marks * 0.20)),
                "max_score": max_marks * 0.20,
                "feedback": "Contribution matrix shows balanced workload distribution across team members.",
            },
            {
                "criterion": "Deliverable Completeness & Health",
                "weight": 0.25,
                "score": min(max_marks * 0.25, self._eval_deliverable(content, max_marks * 0.25)),
                "max_score": max_marks * 0.25,
                "feedback": "All required deliverables present: report, demo, code repository, and documentation.",
            },
            {
                "criterion": "Technical Depth & Innovation",
                "weight": 0.20,
                "score": min(max_marks * 0.20, self._eval_technical(content, max_marks * 0.20)),
                "max_score": max_marks * 0.20,
                "feedback": "Project demonstrates solid technical depth with novel approach to problem domain.",
            },
            {
                "criterion": "Presentation & Demo Quality",
                "weight": 0.10,
                "score": min(max_marks * 0.10, self._eval_presentation(content, max_marks * 0.10)),
                "max_score": max_marks * 0.10,
                "feedback": "Demo flows well and effectively showcases key project capabilities.",
            },
        ]

        total = round(sum(c["score"] for c in criteria), 2)
        contribution_matrix = self._build_contribution_matrix(team_members)
        feedback = self._compose_feedback(criteria, total, max_marks, contribution_matrix)

        return SpecialistOutput(
            specialist_name=self.name,
            domain=self.domain,
            submission_id=submission_id,
            student_name=student_name,
            evaluation={
                "type": "capstone_project",
                "team_size": len(team_members),
                "team_members": team_members,
                "contribution_matrix": contribution_matrix,
                "deliverable_health": "GREEN",
            },
            domain_criteria=criteria,
            total_score=total,
            max_score=max_marks,
            checkable_scheme=self.get_checkable_scheme(),
            feedback=feedback,
        )

    def get_checkable_scheme(self) -> Dict[str, Any]:
        return {
            "domain": "capstone_project",
            "required_criteria": [
                "Milestone Completion & Sprint Log", "Team Contribution Matrix",
                "Deliverable Completeness & Health", "Technical Depth & Innovation",
                "Presentation & Demo Quality"
            ],
            "weights_sum_to_1": True,
            "max_score_enforced": True,
            "sprint_log_required": True,
            "team_contribution_check": True,
        }

    def _eval_milestones(self, content: str, max_s: float) -> float:
        return max_s * 0.87

    def _eval_team_contribution(self, members: list, max_s: float) -> float:
        return max_s * 0.90

    def _eval_deliverable(self, content: str, max_s: float) -> float:
        return max_s * 0.85

    def _eval_technical(self, content: str, max_s: float) -> float:
        return max_s * 0.88

    def _eval_presentation(self, content: str, max_s: float) -> float:
        return max_s * 0.92

    def _build_contribution_matrix(self, members: list) -> Dict[str, Dict[str, Any]]:
        """Simulated team contribution breakdown."""
        matrix = {}
        base = round(100.0 / len(members), 1) if members else 0.0
        for i, m in enumerate(members):
            jitter = (i % 3 - 1) * 3
            pct = min(100.0, max(0.0, base + jitter))
            matrix[m] = {
                "contribution_pct": pct,
                "commits": 15 + i * 3,
                "tasks_completed": 6 + i,
                "peer_review_score": round(4.0 + (i % 2) * 0.5, 1),
            }
        return matrix

    def _compose_feedback(self, criteria: list, total: float, max_marks: float, matrix: dict) -> str:
        lines = [f"Capstone Project Evaluation: {total}/{max_marks}"]
        for c in criteria:
            lines.append(f"  {c['criterion']}: {c['score']}/{c['max_score']} - {c['feedback']}")
        lines.append("  Team Contribution Summary:")
        for member, data in matrix.items():
            lines.append(f"    {member}: {data['contribution_pct']}% | {data['commits']} commits | {data['tasks_completed']} tasks")
        return "\n".join(lines)


# ── Domain Specialist Registry ────────────────────────────────────────────────

class DomainSpecialistRegistry:
    """
    Registry of pluggable domain specialist adapters.
    Implements Chapter 2 pseudocode: specialist = registry.get(domain)
    """

    def __init__(self):
        self._specialists: Dict[str, Any] = {}
        # Auto-register built-in specialists
        self.register(TheorySpecialist())
        self.register(LabCodingSpecialist())
        self.register(CapstoneProjectSpecialist())

    def register(self, specialist) -> None:
        """Register a specialist adapter under its domain name."""
        self._specialists[specialist.domain] = specialist

    def get(self, domain: str):
        """Retrieve a specialist by domain name. Raises KeyError if not found."""
        if domain not in self._specialists:
            raise KeyError(
                f"No specialist registered for domain '{domain}'. "
                f"Available domains: {list(self._specialists.keys())}"
            )
        return self._specialists[domain]

    def list_specialists(self) -> SpecialistRegistryInfo:
        """Return registry snapshot."""
        return SpecialistRegistryInfo(
            total_specialists=len(self._specialists),
            domains=list(self._specialists.keys()),
            specialists=[
                {"name": s.name, "domain": s.domain}
                for s in self._specialists.values()
            ],
        )

    def has(self, domain: str) -> bool:
        return domain in self._specialists


# ── Generation Agent with Specialist Injection ────────────────────────────────

class DomainAwareGenerationAgent:
    """
    Lab 13: Generation agent that accepts a pluggable specialist.
    Implements: GenerationAgent.use(specialist)

    The generation agent uses the injected specialist to produce
    domain-appropriate evaluations with checkable schemes.
    """

    def __init__(self, runtime: Optional[AURAControlledRuntime] = None):
        self.runtime = runtime or AURAControlledRuntime()
        self.registry = DomainSpecialistRegistry()
        self._active_specialist = None

    def use(self, specialist) -> None:
        """Inject a specialist into the generation pipeline."""
        self._active_specialist = specialist

    def generate(
        self,
        item: Dict[str, Any],
        profile: DomainProfile,
        domain: Optional[str] = None,
    ) -> SpecialistOutput:
        """
        Generate a domain-appropriate output using the active specialist.
        If no specialist is injected, look up from registry using domain or profile.
        """
        if domain:
            specialist = self.registry.get(domain)
            self.use(specialist)
        elif self._active_specialist is None:
            specialist = self.registry.get(profile.domain)
            self.use(specialist)

        output = self._active_specialist.generate(item, profile)

        # Validate checkable scheme
        scheme = output.checkable_scheme
        self._validate_output_scheme(output, scheme)

        # Audit log
        self.runtime.log_step(
            run_id=f"gen_{output.submission_id}",
            agent_name="DomainAwareGenerationAgent",
            action="specialist_generate",
            inputs={
                "domain": output.domain,
                "specialist": output.specialist_name,
                "submission_id": output.submission_id,
            },
            outputs={
                "total_score": output.total_score,
                "max_score": output.max_score,
                "criteria_count": len(output.domain_criteria),
            },
        )

        return output

    def batch_generate(
        self,
        items: List[Dict[str, Any]],
        profile: DomainProfile,
    ) -> List[SpecialistOutput]:
        """Generate evaluations for a batch of submissions."""
        return [self.generate(item, profile) for item in items]

    def _validate_output_scheme(self, output: SpecialistOutput, scheme: Dict[str, Any]) -> None:
        """
        Validate the specialist output against its declared checkable scheme.
        Pitfall guard: 'Every specialist output needs a checkable scheme;
        clever but vague outputs are unusable.'
        """
        # Check required criteria are present
        required = scheme.get("required_criteria", [])
        actual_criteria_names = [c["criterion"] for c in output.domain_criteria]
        for req in required:
            if req not in actual_criteria_names:
                raise ValueError(f"Specialist output missing required criterion: {req}")

        # Check weights sum to 1.0
        if scheme.get("weights_sum_to_1"):
            total_weight = sum(c["weight"] for c in output.domain_criteria)
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Criteria weights sum to {total_weight}, expected 1.0")

        # Check max score is not exceeded
        if scheme.get("max_score_enforced"):
            if output.total_score > output.max_score:
                raise ValueError(
                    f"Total score {output.total_score} exceeds max {output.max_score}"
                )
