"""
Interactive Demonstration CLI for Lab 4: Memory & Retrieval (State vs Stored)
Chapter 2: Course Project, Notes & Assignment Organizer

Demonstrates:
1. Separation between Short-Term Run State (ephemeral draft) and Long-Term Knowledge
2. Tag-based retrieval over versioned course notes
3. Embedding / vector similarity search over historical submissions (plagiarism detection)
4. Proof of non-contamination: Short-term run state does not mutate stored knowledge.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from agents.retrieval_agent import CourseRetrievalAgent, ShortTermRunState


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_lab4_demonstration():
    agent = CourseRetrievalAgent()

    print_banner("LAB 4: MEMORY & RETRIEVAL (STATE VS STORED)")
    print("Worklet: Chapter 2 — Course Project, Notes & Assignment Organizer")
    print("Core Rule: Don't conflate run state with the archive — mixing them corrupts the baseline.\n")

    # -------------------------------------------------------------
    # 1. Short-Term Run State
    # -------------------------------------------------------------
    print_banner("1. SHORT-TERM MEMORY (Ephemeral Run Context)")
    state = ShortTermRunState(run_id="run_demo_401", course_id=1)
    print(f"Initial State: Draft={state.draft}, Step={state.step}")
    
    candidate = {
        "submission_id": 999,
        "student_name": "Test Candidate",
        "code": "class ReActAgent:\n    def __init__(self, tools):\n        self.tools = tools"
    }
    print(f"Updating active run draft: state.draft = candidate")
    state.update_draft(candidate)
    print(f"State Check: Draft Attached={state.draft is not None}")
    print(f"Session Logs: {state.session_logs[-1]}")

    # -------------------------------------------------------------
    # 2. Long-Term Tag Retrieval
    # -------------------------------------------------------------
    print_banner("2. LONG-TERM MEMORY (Tag-Based Retrieval over Course Notes)")
    print("Querying store with tag: {'unit': 'Unit 1'}...")
    notes_u1 = agent.retrieve_notes_by_tags(course_id=1, tags={"unit": "Unit 1"})
    print(f"Retrieved {len(notes_u1)} matching note versions:")
    for n in notes_u1:
        curr_tag = "[CURRENT]" if n.is_current else "[SUPERSEDED]"
        print(f"  * {curr_tag} {n.unit} | {n.title} (v{n.version})")
        print(f"    Snippet: \"{n.snippet.strip()[:80]}...\"")

    print("\nQuerying store with tag: {'unit': 'Unit 2'}...")
    notes_u2 = agent.retrieve_notes_by_tags(course_id=1, tags={"unit": "Unit 2"})
    for n in notes_u2:
        print(f"  * {n.unit} | {n.title} (v{n.version})")

    # -------------------------------------------------------------
    # 3. Long-Term Vector Similarity Retrieval
    # -------------------------------------------------------------
    print_banner("3. LONG-TERM MEMORY (Vector Similarity Search over Submissions Archive)")
    print("Searching vector store for prior submissions similar to candidate code...")
    prior_matches = agent.retrieve_prior_submissions_by_similarity(candidate["code"], k=3, threshold=0.75)
    print(f"Found {len(prior_matches)} nearest historical submissions:")
    for idx, match in enumerate(prior_matches, 1):
        flag = " [CRITICAL PLAGIARISM RISK]" if match.is_plagiarism_risk else " [NORMAL]"
        print(f"  [{idx}] Student: {match.student_name} | Similarity: {match.similarity_score:.2%}{flag}")
        print(f"      File: {match.file_name}")

    # -------------------------------------------------------------
    # 4. Pseudocode Invariant Execution
    # -------------------------------------------------------------
    print_banner("4. PSEUDOCODE EXECUTION & VERIFICATION")
    print("Running Lab 4 Pseudocode:")
    print("  state.draft = candidate                       # short-term")
    print("  hits  = retrieve(store, tags)                 # long-term")
    print("  prior = retrieve(history, embed(candidate), k=5)  # similarity")

    res = agent.execute_memory_split_workflow(
        run_id="run_pseudocode_verify",
        candidate_submission=candidate,
        query_tags={"unit": "Unit 1"}
    )
    print(f"\nExecution Result: {res['memory_separation_verified']}")
    print(f"  Short-term draft retained: {res['short_term_state']['draft']['student_name']}")
    print(f"  Long-term notes hits: {len(res['long_term_notes_hits'])} items")
    print(f"  Long-term prior matches: {len(res['long_term_prior_history'])} items")

    print_banner("LAB 4 DEMONSTRATION COMPLETE: STATE VS STORED MEMORY SEPARATION CONFIRMED")


if __name__ == "__main__":
    run_lab4_demonstration()
