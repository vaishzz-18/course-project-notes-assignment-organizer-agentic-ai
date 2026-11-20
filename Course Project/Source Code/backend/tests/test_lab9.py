"""
Acceptance Test Suite for Lab 9: Deep Research — Grounding & Evidence
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Acceptance Criteria:
  • Each candidate carries an evidence record with source citations.
  • A paper-level evidence table is produced.
  • Every accepted output maps to an in-scope source with citations.
  • Ungrounded or out-of-scope candidates are strictly rejected.
  • Works in harmony with AURAControlledRuntime provenance.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.grounding_agent import (
    EvidenceGroundingAgent,
    EvidenceCitation,
    EvidenceRecord,
    GroundedCandidate,
    EvidenceTable,
)
from runtime.governed_runtime import AURAControlledRuntime


class TestLab9GroundingAgent:

    def test_in_scope_candidate_is_grounded_with_citations(self):
        """Valid agentic AI submission must be grounded with in-scope citations."""
        agent = EvidenceGroundingAgent(coverage_threshold=0.50)
        content = (
            "We built an agentic workflow using LangGraph StateGraph with nodes and conditional edges. "
            "The planner loop executes ReAct cycles to clarify and propose plans. "
            "All math operations call typed tools for zero hallucination."
        )

        record = agent.research_candidate(
            candidate_id="cand_test_01",
            content=content,
            candidate_title="Agentic Workflow Assignment",
        )

        assert record.in_scope is True
        assert record.coverage_score >= 0.50
        assert len(record.citations) >= 2
        assert len(record.verified_concepts) >= 3
        assert record.rejection_reason is None

        # Verify citation structure
        citation = record.citations[0]
        assert citation.source_id.startswith("syllabus:") or citation.source_id.startswith("rubric:")
        assert citation.relevance_score > 0.0
        assert len(citation.exact_quote) > 10

    def test_out_of_scope_candidate_is_rejected(self):
        """Out-of-scope content (e.g. quantum annealing) must be strictly rejected."""
        agent = EvidenceGroundingAgent()
        content = (
            "We used D-Wave quantum annealing adiabatic Hamiltonians to calculate student marks. "
            "Quantum superposition states optimize grading allocation."
        )

        candidate = agent.evaluate_submission(
            candidate_id="cand_quantum",
            content=content,
            student_name="Quantum Student",
        )

        assert candidate.status == "REJECTED"
        assert candidate.evidence.in_scope is False
        assert candidate.evidence.rejection_reason is not None
        assert "Quantum computing is outside the CS401" in candidate.evidence.rejection_reason

    def test_insufficient_grounding_coverage_is_rejected(self):
        """Vague content with insufficient syllabus alignment must be rejected."""
        agent = EvidenceGroundingAgent(coverage_threshold=0.50)
        content = "This is a generic essay about software development and writing code on laptops."

        record = agent.research_candidate(
            candidate_id="cand_vague",
            content=content,
        )

        assert record.in_scope is False
        assert record.coverage_score < 0.50
        assert record.rejection_reason is not None

    def test_batch_evaluation_produces_evidence_table(self):
        """Batch evaluation must compile a complete paper-level evidence table."""
        agent = EvidenceGroundingAgent(coverage_threshold=0.50)
        submissions = [
            {
                "id": "sub_1",
                "student_name": "Alex Chen",
                "content": "LangGraph StateGraph nodes with ReAct loops and typed tools zero hallucination."
            },
            {
                "id": "sub_2",
                "student_name": "Priya Sharma",
                "content": "Parallel swarm using asyncio.gather for fan-out worker processing."
            },
            {
                "id": "sub_3",
                "student_name": "Bad Candidate",
                "content": "Ethereum smart contract blockchain mining proof of work tokens."
            }
        ]

        candidates, table = agent.evaluate_batch(
            submissions=submissions,
            course_code="CS401",
            assignment_title="Lab 9 Test Assignment"
        )

        assert len(candidates) == 3
        assert table.total_candidates == 3
        assert table.grounded_count == 2
        assert table.rejected_count == 1
        assert len(table.rows) == 3

        # First two should be grounded, third rejected
        assert candidates[0].status == "GROUNDED"
        assert candidates[1].status == "GROUNDED"
        assert candidates[2].status == "REJECTED"

    def test_controlled_runtime_audit_provenance_integration(self):
        """Grounding actions must log provenance steps in AURAControlledRuntime."""
        runtime = AURAControlledRuntime()
        agent = EvidenceGroundingAgent(runtime=runtime)

        agent.research_candidate(
            candidate_id="run_audit_01",
            content="LangGraph StateGraph with typed tools.",
            candidate_title="Audit Test"
        )

        assert len(runtime.in_memory_audit) >= 1
        last_step = runtime.in_memory_audit[-1]
        assert last_step.agent_name == "EvidenceGroundingAgent"
        assert last_step.action == "ground_candidate"
        assert "in_scope" in last_step.output_data


class TestLab9ApiIntegration:

    def test_lab9_demo_endpoint(self):
        """FastAPI route /lab9/demo must return all acceptance criteria passed."""
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)
        response = client.get("/lab9/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["lab"] == "Lab 9: Deep Research — Ground & Evidence"
        assert data["acceptance_criteria_passed"] is True
        assert data["criteria_detail"]["paper_level_evidence_table_produced"] is True
        assert data["criteria_detail"]["ungrounded_candidates_rejected"] is True
