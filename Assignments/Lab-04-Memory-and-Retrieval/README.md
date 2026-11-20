# Context & Memory — Short-Term State & Semantic Store

**Laboratory Number:** Lab 04  
**Curriculum Phase:** Phase A — Foundations  
**Course Artifact:** Chapter 2. Course Project, Notes & Assignment Organizer (apniLeap AURA)  
**Team Number:** 14  

---

## 1. Objective
Implement an architectural separation between ephemeral short-term conversational run state and persistent long-term academic knowledge retrieval with course-level isolation.

---

## 2. Problem Statement & Task Description
Conflating working session context with long-term syllabus and notes leads to token window exhaustion, context drift, and cross-course data leakage.

---

## 3. Key Concepts Demonstrated
- **Dual-memory architecture (Ephemeral Session vs Persistent Vector Store)**
- **Course-scoped retrieval isolation (strict boundary enforcement)**
- **Unit and chapter tag-based indexing**
- **Citation attribution for retrieved knowledge chunks**

---

## 4. Architecture & Workflow
```mermaid
flowchart LR
    subgraph Short-Term Memory
        SessionState[RunContext State JSON]
        SessionLogs[Session Event Logs]
    end
    subgraph Long-Term Memory
        DocChunks[(Document Chunks 768-dim)]
        NotesStore[(Notes Repository)]
    end
    Query[Academic Query] --> RetrievalAgent[Retrieval Agent]
    RetrievalAgent <--> Short-Term Memory
    RetrievalAgent -->|Course-Scoped Search| Long-Term Memory
```

---

## 5. Implementation Explanation
In the context of the **Course Project, Notes & Assignment Organizer**, Lab 04 establishes critical functional infrastructure:
- The implementation directly leverages the canonical project modules.
- It operates under the universal human-in-the-loop invariant: **"Agents draft, cross-check, diagnose, and flag; a named human faculty member inspects, overrides, and approves."**
- Complete execution state and audit records are preserved for every transaction.

---

## 6. Relevant Source-Code References
The canonical implementation for this laboratory demonstration is integrated directly within the production codebase:
- [`backend/agents/retrieval_agent.py`](../../Course%20Project/Source%20Code/backend/agents/retrieval_agent.py)
- [`backend/services/retrieval_service.py`](../../Course%20Project/Source%20Code/backend/services/retrieval_service.py)
- [`backend/services/embedding_service.py`](../../Course%20Project/Source%20Code/backend/services/embedding_service.py)
- [`backend/lab4_demo.py`](../../Course%20Project/Source%20Code/backend/lab4_demo.py)
- [`backend/tests/test_lab4.py`](../../Course%20Project/Source%20Code/backend/tests/test_lab4.py)
- [`backend/api/routes/lab4.py`](../../Course%20Project/Source%20Code/backend/api/routes/lab4.py)

---

## 7. Execution Procedure
To run the standalone laboratory demonstration and verify its automated test suite, execute the following commands from the project root:

```bash
# 1. Run the standalone interactive CLI demonstration
python backend/lab4_demo.py

# 2. Run the automated pytest suite for Lab 04
pytest backend/tests/test_lab4.py -v
```

---

## 8. Actual Execution Evidence & Output
All 4 test cases in `backend/tests/test_lab4.py` pass:
- `test_lab4_short_term_run_state`: PASSED
- `test_lab4_tag_based_notes_retrieval`: PASSED
- `test_lab4_pseudocode_contract`: PASSED
- `test_lab4_api_integration`: PASSED

---

## 9. Acceptance Criteria
- [x] Short-term session state updates without modifying persistent document storage.
- [x] Retrieval queries strictly filter by `course_id`, guaranteeing cross-course privacy.
- [x] Retrieval results return document citations and relevance scores.

---

## 10. Result & Conclusion
Lab 04 was successfully implemented and verified with **100% test pass rate**. It forms an integral operational component of the overarching AURA multi-agent academic platform.
