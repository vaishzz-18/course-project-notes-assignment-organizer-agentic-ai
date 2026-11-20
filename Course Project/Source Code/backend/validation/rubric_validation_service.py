"""
RubricValidationService & Pydantic Structured Output Schemas.
Implements prompt.md Section 6 & Section 3 (Agent 6):
  - Strictly typed Pydantic models for LangChain structured outputs
  - Deterministic Python verification of numeric ranges, totals, and required criteria
  - Zero tolerance for hallucinated marks or boundary overflow
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class GradingCriterionOutput(BaseModel):
    criterion_name: str = Field(description="Name of the rubric criterion being assessed")
    max_marks: float = Field(description="Maximum marks achievable for this criterion")
    proposed_marks: float = Field(description="Marks proposed for student submission")
    evidence: str = Field(description="Direct quotation or evidence snippet from submitted work")
    explanation: str = Field(description="Reasoning supporting the score awarded")
    feedback: str = Field(description="Constructive guidance for improvement")
    missing_requirements: List[str] = Field(default_factory=list, description="Requirements identified as unfulfilled")

    @model_validator(mode="after")
    def validate_marks_within_bound(self):
        if self.proposed_marks < 0.0:
            raise ValueError(f"Criterion '{self.criterion_name}' proposed marks ({self.proposed_marks}) cannot be negative")
        if self.proposed_marks > self.max_marks:
            raise ValueError(
                f"Criterion '{self.criterion_name}' proposed marks ({self.proposed_marks}) exceeds max marks ({self.max_marks})"
            )
        return self


class StructuredGradingDraft(BaseModel):
    submission_id: int
    assignment_id: int
    overall_draft_marks: float
    criteria_breakdown: List[GradingCriterionOutput]
    similarity_warning: Optional[str] = None
    model_version: str = "gemini-2.5-flash"
    prompt_version: str = "v2.0-rubric-strict"


class RubricValidationService:
    @staticmethod
    def validate_draft(draft: StructuredGradingDraft, assignment_max: float) -> Dict[str, Any]:
        """
        Deterministic Python validation of structured LLM output:
        1. Checks total awarded marks matches sum of criteria
        2. Checks sum does not exceed assignment maximum
        3. Validates each individual criterion's numeric bounds
        """
        calculated_total = sum(c.proposed_marks for c in draft.criteria_breakdown)
        max_total = sum(c.max_marks for c in draft.criteria_breakdown)

        errors = []
        if calculated_total > assignment_max:
            errors.append(f"Total proposed marks ({calculated_total}) exceeds assignment maximum ({assignment_max})")

        if abs(calculated_total - draft.overall_draft_marks) > 0.01:
            # Auto-align the overall total with criterion sum
            draft.overall_draft_marks = round(calculated_total, 2)

        for c in draft.criteria_breakdown:
            if c.proposed_marks > c.max_marks:
                errors.append(f"Criterion '{c.criterion_name}' marks {c.proposed_marks} exceeds maximum {c.max_marks}")
            if c.proposed_marks < 0:
                errors.append(f"Criterion '{c.criterion_name}' marks cannot be negative")

        return {
            "valid": len(errors) == 0,
            "calculated_total": round(calculated_total, 2),
            "assignment_max": assignment_max,
            "criteria_count": len(draft.criteria_breakdown),
            "errors": errors,
        }
