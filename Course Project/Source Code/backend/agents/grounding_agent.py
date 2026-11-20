"""
Lab 9: Deep Research — Grounding & Evidence
Phase C: Applied Reliability
Chapter 2: Course Project, Notes & Assignment Organizer

Core Goal:
Ground every output in cited, in-scope evidence. For each assignment submission,
the agent builds an evidence record grounded in the faculty-approved rubric and syllabus,
so validity is auditable and out-of-scope content cannot slip through.

Acceptance Criteria:
  • Each candidate carries an evidence record with source citations.
  • A paper-level evidence table is produced.
  • Every accepted output maps to an in-scope source with citations.
  • Ungrounded or out-of-scope candidates are strictly rejected.
  • Works in harmony with AURAControlledRuntime provenance.

Pseudocode (from Chapter 2):
  for c in candidates:
      ev = research(c, source='the faculty-approved rubric and syllabus')
      if not ev.in_scope: reject(c)
      c.evidence = ev
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from runtime.governed_runtime import AURAControlledRuntime


# ── Data Models ───────────────────────────────────────────────────────────────

class EvidenceCitation(BaseModel):
    """Specific citation linking a claim or concept to an approved course source."""
    source_id: str = Field(..., description="Unique source identifier (e.g. 'syllabus:cs401', 'rubric:asgn1')")
    source_title: str = Field(..., description="Human-readable title of the approved source")
    source_type: Literal["syllabus", "lecture_notes", "rubric", "reference_material"] = Field(...)
    unit: Optional[str] = Field(None, description="Course unit (e.g. 'Unit 3: LangGraph StateGraphs')")
    criterion_matched: Optional[str] = Field(None, description="Rubric criterion matched if applicable")
    exact_quote: str = Field(..., description="Verified excerpt or exact text quote from the approved source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Confidence/relevance score")


class EvidenceRecord(BaseModel):
    """Complete provenance and evidence record for a candidate output."""
    candidate_id: str
    candidate_title: str
    in_scope: bool = Field(..., description="True if verified against approved sources; False if ungrounded")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Percentage of claims backed by evidence")
    citations: List[EvidenceCitation] = Field(default_factory=list)
    verified_concepts: List[str] = Field(default_factory=list)
    unmatched_concepts: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GroundedCandidate(BaseModel):
    """A candidate output enriched with its evidence record and acceptance status."""
    candidate_id: str
    student_name: Optional[str] = None
    student_id: Optional[int] = None
    content: str
    status: Literal["GROUNDED", "REJECTED", "FLAGGED_FOR_HUMAN_REVIEW"]
    evidence: EvidenceRecord
    faculty_notes: Optional[str] = None


class EvidenceTableRow(BaseModel):
    """One row in the paper-level evidence table."""
    candidate_id: str
    student_name: str
    status: str
    in_scope: bool
    coverage_score: float
    citation_count: int
    primary_source: str
    rejection_reason: Optional[str] = None


class EvidenceTable(BaseModel):
    """Paper-level evidence table aggregating grounding results across all submissions."""
    course_code: str
    course_name: str
    assignment_title: str
    total_candidates: int
    grounded_count: int
    rejected_count: int
    average_coverage: float
    rows: List[EvidenceTableRow]
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Faculty-Approved Knowledge Store ──────────────────────────────────────────

DEFAULT_APPROVED_SYLLABUS = {
    "course_code": "CS401",
    "course_name": "Agentic AI & Autonomous Systems",
    "units": [
        {
            "unit": "Unit 1",
            "title": "Agent vs Chatbot: ReAct Cognitive Loops & Planner Engines",
            "keywords": ["react", "planner", "clarify", "propose", "revise", "lock", "cognitive loop", "course plan", "agentic workflow"],
            "excerpts": [
                "ReAct loops combine reasoning traces with action execution in an iterative loop.",
                "The planner loop clarifies ambiguous user requirements before proposing an editable plan.",
                "Plans become immutable specifications once approved by human authority."
            ]
        },
        {
            "unit": "Unit 2",
            "title": "Tool-Using Agents: Typed Tool Invocations & Zero-Hallucination Math",
            "keywords": ["tools", "pydantic", "zero hallucination", "typed tools", "deadline calculation", "rubric calculator", "similarity check"],
            "excerpts": [
                "Agents must execute mathematical calculations and database lookups exclusively through typed tools.",
                "Zero-hallucination constraint requires that prompts never compute grades or check deadlines directly.",
                "Tool calls are validated via strict Pydantic schemas before execution."
            ]
        },
        {
            "unit": "Unit 3",
            "title": "LangGraph StateGraphs: Directed Agentic Workflows & Back-Edges",
            "keywords": ["langgraph", "stategraph", "nodes", "edges", "back-edge", "self-healing", "conditional routing", "human-in-the-loop"],
            "excerpts": [
                "LangGraph StateGraph coordinates complex multi-agent execution using typed state dictionaries.",
                "Conditional back-edges allow validation failures to re-route execution back to specialized workers for bounded retries.",
                "FacultyGate acts as an explicit human-in-the-loop interruption point before publishing."
            ]
        },
        {
            "unit": "Unit 4",
            "title": "Parallel Multi-Agent Swarms: Fan-Out & Plan-Aligned Merge",
            "keywords": ["swarm", "parallel", "fan-out", "fan-in", "asyncio.gather", "worker pool", "merge", "speedup"],
            "excerpts": [
                "Parallel swarms utilize asyncio.gather to evaluate student submission batches concurrently.",
                "The fan-in coordinator merges specialist results strictly aligned to the locked course plan.",
                "Wall-clock speedup factor benchmarks parallel swarm execution against sequential processing."
            ]
        }
    ],
    "rubric_criteria": [
        {
            "criterion": "Agentic Architecture & ReAct Loops",
            "max_marks": 25.0,
            "description": "Clear implementation of Reason+Act cycles with typed inputs and outputs"
        },
        {
            "criterion": "Tool Calling & Zero-Hallucination Invariants",
            "max_marks": 25.0,
            "description": "Validation that all mathematical computations and state queries invoke registered tools"
        },
        {
            "criterion": "StateGraph Topology & Nodes",
            "max_marks": 25.0,
            "description": "Proper LangGraph encapsulation across discrete specialist nodes with conditional back-edges"
        },
        {
            "criterion": "Swarm Parallelism & Provenance Audit",
            "max_marks": 25.0,
            "description": "Demonstration of concurrent fan-out worker processing and complete audit logging"
        }
    ]
}


# ── Evidence Grounding Agent Implementation ───────────────────────────────────

class EvidenceGroundingAgent:
    """
    Lab 9: Deep Research — Evidence Grounding Agent.
    
    Verifies that candidate assignment submissions, grading feedback, and lecture summaries
    are strictly grounded in faculty-approved syllabus topics, unit lecture materials,
    and official assignment rubrics.
    
    Rejects ungrounded or out-of-scope candidates with clear diagnostic rationales.
    """

    def __init__(
        self,
        approved_syllabus: Optional[Dict[str, Any]] = None,
        runtime: Optional[AURAControlledRuntime] = None,
        coverage_threshold: float = 0.50
    ):
        self.syllabus = approved_syllabus or DEFAULT_APPROVED_SYLLABUS
        self.runtime = runtime
        self.coverage_threshold = coverage_threshold

    def research_candidate(
        self,
        candidate_id: str,
        content: str,
        candidate_title: str = "Assignment Submission",
        student_name: str = "Anonymous Student",
        student_id: Optional[int] = None,
    ) -> EvidenceRecord:
        """
        Deeply inspects candidate text against the approved syllabus units and rubrics.
        Extracts citations, computes coverage, and determines in-scope status.
        """
        content_lower = content.lower()
        citations: List[EvidenceCitation] = []
        verified_concepts: List[str] = []
        unmatched_concepts: List[str] = []

        # 1. Check against syllabus units
        total_unit_keywords = 0
        matched_unit_keywords = 0

        for unit_info in self.syllabus.get("units", []):
            unit_title = unit_info.get("title", "")
            unit_name = unit_info.get("unit", "")
            keywords = unit_info.get("keywords", [])
            total_unit_keywords += len(keywords)

            unit_matches = []
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", content_lower):
                    unit_matches.append(kw)
                    if kw not in verified_concepts:
                        verified_concepts.append(kw)

            matched_unit_keywords += len(unit_matches)

            # If unit has matching concepts, attach evidence citation from approved excerpt
            if unit_matches:
                matching_excerpts = [
                    ex for ex in unit_info.get("excerpts", [])
                    if any(m in ex.lower() for m in unit_matches)
                ]
                quote = matching_excerpts[0] if matching_excerpts else unit_info.get("excerpts", [""])[0]
                relevance = min(1.0, len(unit_matches) / 2.0)

                citations.append(
                    EvidenceCitation(
                        source_id=f"syllabus:{unit_name.lower().replace(' ', '_')}",
                        source_title=f"{self.syllabus.get('course_code')}: {unit_title}",
                        source_type="lecture_notes",
                        unit=f"{unit_name}: {unit_title}",
                        exact_quote=quote,
                        relevance_score=round(relevance, 2),
                    )
                )

        # 2. Check against rubric criteria
        for rubric_item in self.syllabus.get("rubric_criteria", []):
            crit_name = rubric_item.get("criterion", "")
            crit_desc = rubric_item.get("description", "")
            # Check for concept overlap with criterion description
            words = [w.lower() for w in re.findall(r"\b\w{4,}\b", crit_desc)]
            matches = [w for w in words if w in content_lower]
            if len(matches) >= 2:
                citations.append(
                    EvidenceCitation(
                        source_id=f"rubric:{crit_name.lower().replace(' ', '_')[:20]}",
                        source_title="Faculty-Approved Assignment Rubric",
                        source_type="rubric",
                        criterion_matched=crit_name,
                        exact_quote=f"Criterion: {crit_name} (Max: {rubric_item.get('max_marks')}) — {crit_desc}",
                        relevance_score=round(min(1.0, len(matches) / 4.0), 2),
                    )
                )

        # 3. Detect known hallucinated / out-of-scope concepts
        out_of_scope_patterns = [
            ("quantum annealing", "Quantum computing is outside the CS401 Agentic AI syllabus"),
            ("blockchain mining", "Cryptocurrency consensus is outside the CS401 Agentic AI syllabus"),
            ("protein folding", "Bioinformatics/AlphaFold is outside the CS401 Agentic AI syllabus"),
            ("smart contract", "Web3 smart contracts are outside the CS401 Agentic AI syllabus"),
            ("unrelated essay", "Content does not address agentic workflow specifications"),
        ]

        for bad_kw, reason in out_of_scope_patterns:
            if bad_kw in content_lower:
                unmatched_concepts.append(f"OUT-OF-SCOPE: '{bad_kw}' — {reason}")

        # Compute coverage score
        if verified_concepts:
            # Baseline coverage scaled to expectation
            raw_coverage = min(1.0, len(verified_concepts) / 4.0)
        else:
            raw_coverage = 0.0

        # Determine in-scope:
        # A candidate is REJECTED if:
        # 1. It contains fatal out-of-scope concepts
        # 2. Coverage score is below the threshold
        # 3. It has zero verified citations
        has_fatal_out_of_scope = len(unmatched_concepts) > 0
        in_scope = (raw_coverage >= self.coverage_threshold) and not has_fatal_out_of_scope and len(citations) > 0

        rejection_reason = None
        if not in_scope:
            if has_fatal_out_of_scope:
                rejection_reason = "; ".join(unmatched_concepts)
            elif len(citations) == 0:
                rejection_reason = "Zero citations mapped to faculty-approved syllabus or rubric."
            else:
                rejection_reason = f"Insufficient grounding coverage ({raw_coverage*100:.1f}% < {self.coverage_threshold*100:.1f}% threshold)."

        record = EvidenceRecord(
            candidate_id=candidate_id,
            candidate_title=candidate_title,
            in_scope=in_scope,
            coverage_score=round(raw_coverage, 2),
            citations=citations,
            verified_concepts=verified_concepts,
            unmatched_concepts=unmatched_concepts,
            rejection_reason=rejection_reason,
        )

        # Provenance audit logging if runtime attached
        if self.runtime:
            self.runtime.log_step(
                run_id=candidate_id,
                agent_name="EvidenceGroundingAgent",
                action="ground_candidate",
                inputs={"candidate_id": candidate_id, "title": candidate_title},
                outputs={"in_scope": in_scope, "coverage": record.coverage_score, "citations": len(citations)},
            )

        return record

    def evaluate_submission(
        self,
        candidate_id: str,
        content: str,
        student_name: str,
        student_id: Optional[int] = None,
        candidate_title: str = "Lab Assignment Submission"
    ) -> GroundedCandidate:
        """
        Evaluates a single candidate and returns a GroundedCandidate object.
        Rejects ungrounded or out-of-scope candidates.
        """
        evidence = self.research_candidate(
            candidate_id=candidate_id,
            content=content,
            candidate_title=candidate_title,
            student_name=student_name,
            student_id=student_id,
        )

        status = "GROUNDED" if evidence.in_scope else "REJECTED"

        return GroundedCandidate(
            candidate_id=candidate_id,
            student_name=student_name,
            student_id=student_id,
            content=content,
            status=status,
            evidence=evidence,
            faculty_notes="Approved for grading pipeline" if evidence.in_scope else f"Rejected by Grounding Agent: {evidence.rejection_reason}"
        )

    def evaluate_batch(
        self,
        submissions: List[Dict[str, Any]],
        course_code: str = "CS401",
        course_name: str = "Agentic AI & Autonomous Systems",
        assignment_title: str = "Assignment 1: Agentic Workflow Architecture"
    ) -> Tuple[List[GroundedCandidate], EvidenceTable]:
        """
        Executes the Chapter 2 grounding loop over a batch of submissions:
          for c in candidates:
              ev = research(c, source='the faculty-approved rubric and syllabus')
              if not ev.in_scope: reject(c)
              c.evidence = ev
        Compiles the paper-level evidence table.
        """
        candidates: List[GroundedCandidate] = []
        table_rows: List[EvidenceTableRow] = []

        for sub in submissions:
            cid = str(sub.get("id") or sub.get("candidate_id") or uuid.uuid4().hex[:8])
            sname = sub.get("student_name", "Anonymous Student")
            sid = sub.get("student_id")
            content = sub.get("content", "")
            title = sub.get("title", f"Submission for {assignment_title}")

            candidate = self.evaluate_submission(
                candidate_id=cid,
                content=content,
                student_name=sname,
                student_id=sid,
                candidate_title=title,
            )
            candidates.append(candidate)

            # Determine primary source citation
            primary_source = (
                candidate.evidence.citations[0].source_title
                if candidate.evidence.citations
                else "None (Ungrounded)"
            )

            table_rows.append(
                EvidenceTableRow(
                    candidate_id=candidate.candidate_id,
                    student_name=sname,
                    status=candidate.status,
                    in_scope=candidate.evidence.in_scope,
                    coverage_score=candidate.evidence.coverage_score,
                    citation_count=len(candidate.evidence.citations),
                    primary_source=primary_source,
                    rejection_reason=candidate.evidence.rejection_reason,
                )
            )

        grounded_count = sum(1 for c in candidates if c.status == "GROUNDED")
        rejected_count = sum(1 for c in candidates if c.status == "REJECTED")
        avg_coverage = (
            sum(c.evidence.coverage_score for c in candidates) / len(candidates)
            if candidates else 0.0
        )

        table = EvidenceTable(
            course_code=course_code,
            course_name=course_name,
            assignment_title=assignment_title,
            total_candidates=len(candidates),
            grounded_count=grounded_count,
            rejected_count=rejected_count,
            average_coverage=round(avg_coverage, 2),
            rows=table_rows,
        )

        return candidates, table


# Backward compatibility alias
GroundingAgent = EvidenceGroundingAgent
