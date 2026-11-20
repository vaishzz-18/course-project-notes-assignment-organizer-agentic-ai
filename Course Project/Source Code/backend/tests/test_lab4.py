"""
Acceptance Test Suite for Lab 4: Memory & Retrieval — State vs Stored
Verifies:
1. Separation between short-term run state (ephemeral session context) and long-term stored archives.
2. Tag-based retrieval over versioned course notes repository.
3. Embedding/vector similarity retrieval over submission history (identifies high-similarity prior work).
4. Pseudocode contract verification:
   state.draft = candidate
   hits = retrieve(store, tags)
   prior = retrieve(history, embed(candidate), k=5)
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.retrieval_agent import CourseRetrievalAgent, ShortTermRunState


def test_lab4_short_term_run_state():
    """Acceptance Test 1: Short-term run state holds active draft without corrupting long-term store."""
    state = ShortTermRunState(run_id="run_test_101", course_id=1)
    assert state.draft is None
    
    candidate = {"id": 101, "student": "Alex Chen", "code": "class ReActAgent: pass"}
    state.update_draft(candidate)

    assert state.draft is not None
    assert state.draft["student"] == "Alex Chen"
    assert len(state.session_logs) >= 1
    
    state.clear()
    assert state.draft is None
    print("\n[PASS] Short-term run state verified: ephemeral lifecycle decoupled from disk.")


def test_lab4_tag_based_notes_retrieval():
    """Acceptance Test 2: Long-term store retrieves notes matching exact metadata tags."""
    agent = CourseRetrievalAgent()
    
    # Query Unit 1
    hits_u1 = agent.retrieve_notes_by_tags(course_id=1, tags={"unit": "Unit 1"})
    assert len(hits_u1) >= 1
    assert all(h.unit == "Unit 1" for h in hits_u1)
    assert hits_u1[0].version == 2  # Current version is v2
    assert "Foundations" in hits_u1[0].title

    # Query Unit 2
    hits_u2 = agent.retrieve_notes_by_tags(course_id=1, tags={"unit": "Unit 2"})
    assert len(hits_u2) >= 1
    assert all(h.unit == "Unit 2" for h in hits_u2)
    assert "MCP" in hits_u2[0].title
    print(f"\n[PASS] Tag retrieval verified: Unit 1 ({len(hits_u1)} hits), Unit 2 ({len(hits_u2)} hits).")


def test_lab4_vector_similarity_retrieval_over_history():
    """Acceptance Test 3: Vector similarity retrieves closest matching prior submissions."""
    agent = CourseRetrievalAgent()

    # Candidate submission code that heavily copies Alex Chen's ReAct code
    plagiarized_candidate = """
    # ReAct implementation copy
    class ReActAgent:
        def __init__(self, tools):
            self.tools = tools
            self.memory = []
        def reason_and_act(self, query):
            for tool in self.tools:
                if tool.can_handle(query):
                    return tool.execute(query)
    """

    prior_hits = agent.retrieve_prior_submissions_by_similarity(plagiarized_candidate, k=3, threshold=0.75)
    assert len(prior_hits) >= 1

    top_hit = prior_hits[0]
    print(f"\n[PASS] Vector similarity retrieval: Top match is '{top_hit.student_name}' with score {top_hit.similarity_score:.2%}")
    assert top_hit.similarity_score >= 0.70, "Should detect high similarity to existing ReAct agent submission."
    assert top_hit.is_plagiarism_risk, "High similarity must flag plagiarism risk!"


def test_lab4_pseudocode_contract():
    """
    Acceptance Test 4: Verifies exact pseudocode:
    state.draft = candidate
    hits = retrieve(store, tags)
    prior = retrieve(history, embed(candidate), k=5)
    """
    agent = CourseRetrievalAgent()
    candidate = {
        "id": 999,
        "student_name": "Test Student",
        "code": "def execute(): return 'Calculated accurately with tools'"
    }

    res = agent.execute_memory_split_workflow(
        run_id="run_lab4_verify",
        candidate_submission=candidate,
        query_tags={"unit": "Unit 1"}
    )

    assert res["memory_separation_verified"]
    assert res["short_term_state"]["draft"]["id"] == 999
    assert len(res["long_term_notes_hits"]) >= 1
    assert len(res["long_term_prior_history"]) >= 1
    print("\n[PASS] Lab 4 Pseudocode contract verified: state vs stored memory separation confirmed.")


if __name__ == "__main__":
    test_lab4_short_term_run_state()
    test_lab4_tag_based_notes_retrieval()
    test_lab4_vector_similarity_retrieval_over_history()
    test_lab4_pseudocode_contract()
    print("\nALL LAB 4 ACCEPTANCE TESTS PASSED!")
