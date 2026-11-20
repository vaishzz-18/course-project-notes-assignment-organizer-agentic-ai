"""
Acceptance Test Suite for Lab 13: Discipline-Specific Agents — Domain Specialisation
Phase D: Governance & Capstone
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  * Pluggable specialist registry with theory, lab_coding, capstone_project domains.
  * specialist = registry.get(domain) returns correct specialist.
  * Each specialist produces domain-appropriate outputs with checkable schemes.
  * Weights sum to 1.0, scores never exceed max, all required criteria present.
  * GenerationAgent.use(specialist) injection pattern works for all domains.
  * Unknown domain raises KeyError.
  * Batch evaluation produces outputs for all submissions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.specialists import (
    DomainAwareGenerationAgent,
    DomainSpecialistRegistry,
    DomainProfile,
    SpecialistOutput,
    TheorySpecialist,
    LabCodingSpecialist,
    CapstoneProjectSpecialist,
)


@pytest.fixture
def registry():
    return DomainSpecialistRegistry()


@pytest.fixture
def agent():
    return DomainAwareGenerationAgent()


@pytest.fixture
def theory_profile():
    return DomainProfile(
        domain="theory",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )


@pytest.fixture
def coding_profile():
    return DomainProfile(
        domain="lab_coding",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )


@pytest.fixture
def capstone_profile():
    return DomainProfile(
        domain="capstone_project",
        course_code="CS401",
        course_name="Agentic AI & Autonomous Systems",
    )


class TestDomainSpecialistRegistry:

    def test_registry_has_three_built_in_specialists(self, registry):
        """Registry auto-registers theory, lab_coding, and capstone_project."""
        info = registry.list_specialists()
        assert info.total_specialists == 3
        assert set(info.domains) == {"theory", "lab_coding", "capstone_project"}

    def test_registry_get_returns_correct_specialist(self, registry):
        """registry.get(domain) returns the matching specialist."""
        theory = registry.get("theory")
        assert isinstance(theory, TheorySpecialist)

        coding = registry.get("lab_coding")
        assert isinstance(coding, LabCodingSpecialist)

        capstone = registry.get("capstone_project")
        assert isinstance(capstone, CapstoneProjectSpecialist)

    def test_registry_unknown_domain_raises_keyerror(self, registry):
        """Unknown domain must raise KeyError with helpful message."""
        with pytest.raises(KeyError, match="No specialist registered"):
            registry.get("quantum_physics")

    def test_registry_has_method(self, registry):
        """has() returns True for registered domains, False otherwise."""
        assert registry.has("theory") is True
        assert registry.has("nonexistent") is False


class TestTheorySpecialist:

    def test_theory_produces_five_criteria(self, agent, theory_profile):
        """Theory specialist must produce exactly 5 evaluation criteria."""
        item = {"submission_id": "sub_t1", "student_name": "Student A", "content": "An essay on AI."}
        output = agent.generate(item, theory_profile, domain="theory")
        assert len(output.domain_criteria) == 5

    def test_theory_weights_sum_to_one(self, agent, theory_profile):
        """All criteria weights must sum to 1.0."""
        item = {"submission_id": "sub_t2", "student_name": "Student A", "content": "Essay."}
        output = agent.generate(item, theory_profile, domain="theory")
        total_weight = sum(c["weight"] for c in output.domain_criteria)
        assert abs(total_weight - 1.0) < 0.01

    def test_theory_score_does_not_exceed_max(self, agent, theory_profile):
        """Total score must never exceed max marks."""
        item = {"submission_id": "sub_t3", "student_name": "Student A", "content": "Essay."}
        output = agent.generate(item, theory_profile, domain="theory")
        assert output.total_score <= output.max_score

    def test_theory_checkable_scheme_valid(self, agent, theory_profile):
        """Theory checkable scheme has required fields."""
        item = {"submission_id": "sub_t4", "student_name": "Student A", "content": "Essay."}
        output = agent.generate(item, theory_profile, domain="theory")
        scheme = output.checkable_scheme
        assert scheme["domain"] == "theory"
        assert scheme["citation_check_required"] is True
        assert len(scheme["required_criteria"]) == 5


class TestLabCodingSpecialist:

    def test_coding_produces_five_criteria(self, agent, coding_profile):
        """Lab/Coding specialist must produce exactly 5 evaluation criteria."""
        item = {"submission_id": "sub_c1", "student_name": "Student B", "content": "def foo(): pass"}
        output = agent.generate(item, coding_profile, domain="lab_coding")
        assert len(output.domain_criteria) == 5

    def test_coding_detects_language_and_loc(self, agent, coding_profile):
        """Evaluation includes language detection and lines of code."""
        code = "class Agent:\n    def run(self):\n        pass\n"
        item = {"submission_id": "sub_c2", "student_name": "Student B", "content": code}
        output = agent.generate(item, coding_profile, domain="lab_coding")
        assert output.evaluation["language_detected"] == "python"
        assert output.evaluation["lines_of_code"] == 4
        assert output.evaluation["syntax_valid"] is True

    def test_coding_checkable_scheme_requires_tests(self, agent, coding_profile):
        """Coding scheme must require test execution validation."""
        item = {"submission_id": "sub_c3", "student_name": "Student B", "content": "pass"}
        output = agent.generate(item, coding_profile, domain="lab_coding")
        assert output.checkable_scheme["test_execution_required"] is True
        assert output.checkable_scheme["syntax_validation_required"] is True


class TestCapstoneProjectSpecialist:

    def test_capstone_produces_five_criteria(self, agent, capstone_profile):
        """Capstone specialist must produce exactly 5 evaluation criteria."""
        item = {
            "submission_id": "sub_p1",
            "student_name": "Student C",
            "content": "Sprint 4 complete.",
            "team_members": ["A", "B", "C"],
        }
        output = agent.generate(item, capstone_profile, domain="capstone_project")
        assert len(output.domain_criteria) == 5

    def test_capstone_includes_team_contribution_matrix(self, agent, capstone_profile):
        """Capstone evaluation must include team contribution matrix."""
        members = ["Alice", "Bob", "Charlie"]
        item = {
            "submission_id": "sub_p2",
            "student_name": "Alice",
            "content": "Project deliverable.",
            "team_members": members,
        }
        output = agent.generate(item, capstone_profile, domain="capstone_project")
        matrix = output.evaluation.get("contribution_matrix", {})
        assert len(matrix) == 3
        for member in members:
            assert member in matrix
            assert "contribution_pct" in matrix[member]
            assert "commits" in matrix[member]

    def test_capstone_deliverable_health(self, agent, capstone_profile):
        """Capstone evaluation reports deliverable health status."""
        item = {
            "submission_id": "sub_p3",
            "student_name": "Student D",
            "content": "All deliverables complete.",
            "team_members": ["X", "Y"],
        }
        output = agent.generate(item, capstone_profile, domain="capstone_project")
        assert output.evaluation["deliverable_health"] == "GREEN"

    def test_capstone_checkable_scheme_requires_sprint_log(self, agent, capstone_profile):
        """Capstone scheme must require sprint log and team contribution check."""
        item = {
            "submission_id": "sub_p4",
            "student_name": "Student E",
            "content": "Done.",
            "team_members": ["Z"],
        }
        output = agent.generate(item, capstone_profile, domain="capstone_project")
        assert output.checkable_scheme["sprint_log_required"] is True
        assert output.checkable_scheme["team_contribution_check"] is True


class TestGenerationAgentUsePattern:

    def test_use_injection_switches_specialist(self, agent, theory_profile, coding_profile):
        """GenerationAgent.use(specialist) changes active specialist."""
        theory_spec = TheorySpecialist()
        agent.use(theory_spec)
        out1 = agent.generate({"submission_id": "s1", "student_name": "A", "content": "x"}, theory_profile)
        assert out1.specialist_name == "TheorySpecialist"

        coding_spec = LabCodingSpecialist()
        agent.use(coding_spec)
        out2 = agent.generate({"submission_id": "s2", "student_name": "B", "content": "y"}, coding_profile)
        assert out2.specialist_name == "LabCodingSpecialist"

    def test_batch_generate_all_outputs(self, agent, theory_profile):
        """Batch generation produces one output per submission."""
        items = [
            {"submission_id": f"sub_b{i}", "student_name": f"Student {i}", "content": f"Essay {i}"}
            for i in range(5)
        ]
        results = agent.batch_generate(items, theory_profile)
        assert len(results) == 5
        for r in results:
            assert isinstance(r, SpecialistOutput)
            assert r.total_score <= r.max_score


class TestLab13ApiIntegration:

    def test_lab13_demo_endpoint(self):
        """FastAPI route /lab13/demo must return all domain evaluations."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab13/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["lab"] == "Lab 13: Discipline-Specific Agents — Domain Specialisation"

        steps = data["steps"]
        # Registry has 3 specialists
        assert steps["step1_registry"]["total_specialists"] == 3
        # All 3 domains evaluated
        assert "theory" in steps["step2_theory_evaluation"]["specialist"].lower()
        assert "coding" in steps["step3_lab_coding_evaluation"]["specialist"].lower()
        assert "capstone" in steps["step4_capstone_evaluation"]["specialist"].lower()
        # Scheme validation all passed
        assert steps["step5_scheme_validation"]["theory_scheme_valid"] is True
