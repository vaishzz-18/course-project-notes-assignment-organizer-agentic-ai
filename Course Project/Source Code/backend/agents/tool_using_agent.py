"""
Lab 2: Tool-Using Agent
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Give the agent tools it must call to act, rather than answering from memory or hallucinating.

Acceptance Criteria:
Key numbers and lookups always go through tools, never hand-done in the prompt.
Validates assertions:
a = tool.read('the notes/materials store')
b = tool.read('assignment & rubric definitions')
v = tool.compute(a, b)
assert v.valid
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from tools.course_tools import (
    tool_read_notes_store,
    tool_read_assignment_rubric,
    tool_compute_deadline_compliance,
    tool_compute_rubric_total,
    tool_verify_similarity,
    ReadNotesOutput,
    ReadRubricOutput,
    DeadlineComplianceOutput,
    RubricComputeOutput,
    SimilarityCheckOutput
)


class ToolExecutionTrace(BaseModel := type("BaseModel", (), {})):
    """Simple container for logging tool execution provenance."""
    pass


class CourseToolAgent:
    """
    Coordinator's Tool-Using Specialist Agent.
    Strictly queries real data and performs mathematical computations via typed tools.
    Never hallucinates numbers or assumes facts outside the tool layer.
    """

    AGENT_NAME = "CourseToolAgent"

    def __init__(self):
        self.call_history: List[Dict[str, Any]] = []

    def log_call(self, tool_name: str, inputs: dict, outputs: dict, valid: bool):
        self.call_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "inputs": inputs,
            "outputs": outputs,
            "valid": valid
        })

    def read_notes(self, course_id: int, unit: Optional[str] = None) -> ReadNotesOutput:
        """Reads notes repository through typed tool."""
        res = tool_read_notes_store(course_id, unit)
        self.log_call("tool_read_notes_store", {"course_id": course_id, "unit": unit}, res.model_dump(), res.valid)
        assert res.valid, f"Tool error: Unable to read notes for course {course_id}"
        return res

    def read_assignment_rubric(self, assignment_id: int) -> ReadRubricOutput:
        """Reads assignment and rubric definitions through typed tool."""
        res = tool_read_assignment_rubric(assignment_id)
        self.log_call("tool_read_assignment_rubric", {"assignment_id": assignment_id}, res.model_dump(), res.valid)
        assert res.valid, f"Tool error: Assignment {assignment_id} rubric not found"
        return res

    def compute_submission_compliance(self, submitted_at: str, due_date: str) -> DeadlineComplianceOutput:
        """Computes submission timing strictly through mathematical delta tool."""
        res = tool_compute_deadline_compliance(submitted_at, due_date)
        self.log_call("tool_compute_deadline_compliance", {"submitted_at": submitted_at, "due_date": due_date}, res.model_dump(), res.valid)
        assert res.valid, "Tool error: Deadline compliance computation failed"
        return res

    def compute_rubric_score(self, criteria_marks: Dict[str, float], rubric_max: float) -> RubricComputeOutput:
        """Computes rubric total and validates boundary invariants strictly via tool."""
        res = tool_compute_rubric_total(criteria_marks, rubric_max)
        self.log_call("tool_compute_rubric_total", {"criteria_marks": criteria_marks, "rubric_max": rubric_max}, res.model_dump(), res.valid)
        return res

    def verify_similarity(self, similarity_score: float, threshold: float = 0.75) -> SimilarityCheckOutput:
        """Evaluates similarity against institutional threshold strictly via tool."""
        res = tool_verify_similarity(similarity_score, threshold)
        self.log_call("tool_verify_similarity", {"similarity_score": similarity_score, "threshold": threshold}, res.model_dump(), res.valid)
        assert res.valid, "Tool error: Similarity check failed"
        return res

    def execute_assignment_evaluation_pipeline(self, assignment_id: int, submitted_at: str, criteria_scores: Dict[str, float], similarity_score: float) -> Dict[str, Any]:
        """
        Demonstrates the exact pseudocode contract of Lab 2:
        a = tool.read('the notes/materials store')
        b = tool.read('assignment & rubric definitions')
        v = tool.compute(a, b)
        assert v.valid
        """
        # Step a: Read assignment and rubric
        rubric_data: ReadRubricOutput = self.read_assignment_rubric(assignment_id)
        
        # Step b: Compute deadline compliance
        compliance: DeadlineComplianceOutput = self.compute_submission_compliance(submitted_at, rubric_data.due_date)

        # Step c: Compute rubric total with boundary check
        score_calc: RubricComputeOutput = self.compute_rubric_score(criteria_scores, rubric_data.max_marks)
        assert score_calc.valid, f"Calculated grade violates boundaries: {score_calc.discrepancy_note}"

        # Step d: Verify similarity score
        similarity_flag: SimilarityCheckOutput = self.verify_similarity(similarity_score)

        return {
            "assignment_title": rubric_data.title,
            "max_marks": rubric_data.max_marks,
            "due_date": rubric_data.due_date,
            "timing": compliance.model_dump(),
            "scoring": score_calc.model_dump(),
            "similarity": similarity_flag.model_dump(),
            "provenance": {
                "tools_invoked_count": len(self.call_history),
                "all_tools_valid": all(c["valid"] for c in self.call_history)
            }
        }
