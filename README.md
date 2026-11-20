# Course Project, Notes & Assignment Organizer (apniLeap AURA)

[![Python 3.12 | 3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![Model Context Protocol](https://img.shields.io/badge/Protocol-FastMCP-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Test Suite](https://img.shields.io/badge/Tests-154%20Passed%20(100%25)-brightgreen.svg)]()

> **Final Academic Course Project Submission — Agentic AI (26ECAC401)**  
> **Assigned Artifact:** Chapter 2. Course Project, Notes & Assignment Organizer  
> **Target Production System:** apniLeap AURA (Academic Utility & Resilience Agent)  

---

## Team Details

**Team Number:** 14  
**Division:** B  
**Academic Course:** Agentic AI (`26ECAC401`)  
**Artifact Assigned:** Chapter 2. Course Project, Notes & Assignment Organizer  

| Sl. No. | Student Name | USN | Division | Role / Contribution |
|:---:|:---|:---:|:---:|:---|
| 1 | **Amrutavarshini B** | `01FE23BCI024` | B | Multi-Agent Orchestration & LangGraph Pipelines |
| 2 | **Pooja Pattar** | `01FE23BCI058` | B | FastMCP Server, Connectors & API Gateways |
| 3 | **Vaishnavi Pagad** | `01FE23BCI063` | B | Full-Stack UI/UX, React Portal & Dashboard |
| 4 | **Vaishnavi Kudlamath** | `01FE23BCI012` | B | Governance, Anti-Plagiarism & Verification Testing |

---

## 1. Project Overview

**apniLeap AURA** is an enterprise-grade multi-agent academic operating system built for university departments, instructors, and students. Developed as the complete reference implementation of Chapter 2 ("Course Project, Notes & Assignment Organizer") of the curriculum build-book, AURA unifies the three core academic management streams under a coordinator-worker multi-agent architecture:

1. **Versioned Notes & Knowledge Management:** Ingests syllabus documents, lecture slides, and notes in PDF, DOCX, and text formats. Automatically generates unit/chapter outlines, preserves full parent-child document version history with one-click rollback, and indexes document chunks into 768-dimensional vector embeddings for course-isolated semantic search.
2. **Assignment Distribution & Governed Grading:** Manages assignment lifecycles with multi-criteria rubrics, authoritative deadline timestamping, SHA-256 file integrity validation, pairwise TF-IDF plagiarism detection, Google Gemini AI draft grading, and an immutable Faculty Approval Gate.
3. **Capstone Project & Milestone Tracking:** Tracks student project groups, deliverables, commit progress, milestone health indicators (green/amber/red), and direct faculty codebase feedback.

### Guiding Design Invariant
> **"Agents draft, cross-check, diagnose, and flag; a named human faculty member inspects, overrides, and approves."**  
> Autonomous agents cannot publish grades, modify final marks, or release course materials without explicit faculty sign-off.

---

## 2. Problem Statement

Modern university engineering programs face significant operational friction across semester courses:
- **Fragmented Materials:** Lecture notes and syllabus updates are shared across ad-hoc channels (email, cloud drives, messaging apps), leading to confusion regarding the authoritative version.
- **Grading Fatigue & Inconsistency:** Manually grading hundreds of complex student code submissions and reports against multi-criteria rubrics causes evaluation drift across sections.
- **Hallucination in Auto-Graders:** Naive LLM solutions frequently hallucinate marks, violate maximum score ceilings, or invent ungrounded critique.
- **Plagiarism Omission:** Pairwise cross-submission plagiarism checks are frequently skipped or executed inconsistently due to time constraints.
- **Unmonitored Projects:** Semester capstone team projects lack continuous progress monitoring, leaving faculty unaware of lagging teams until final submission deadlines.

---

## 3. Project Objectives

- **Unified Academic Operations:** Consolidate notes versioning, assignment distribution, similarity checking, and milestone tracking into a cohesive portal and REST API.
- **Deterministic Numerical Accuracy:** Replace LLM arithmetic with typed tools and sandboxed Python execution to ensure 100% mathematical accuracy.
- **Evidence-Grounded AI Scoring:** Evaluate student submissions strictly against faculty-approved rubric criteria, citing exact evidence passages and generating actionable feedback.
- **Strict Human-in-the-Loop Governance:** Enforce a hard stop at the Faculty Gate (`node_faculty_gate`) where drafts remain unreleased until approved by an instructor.
- **Pedagogical 15-Lab Curriculum Workbench:** Integrate the complete progressive 15-module curriculum demonstrating Agentic AI engineering from ReAct planning to parallel swarms and live adversarial defense.

---

## 4. Key Features

- **Notes Repository & Version Control:** Parent-child document lineage with atomic version restoration and course-isolated semantic vector retrieval (`GET /notes/courses/{id}/search`).
- **Assignment Distribution:** Structured assignment brief generation with Pydantic v2 numeric rubric verification (`criteria_sum == max_marks`).
- **Authoritative Submission Intake:** Idempotent submission uploads, late delta calculations, and SHA-256 tamper-evident checksums.
- **Pairwise TF-IDF Plagiarism Screening:** Automated cross-submission similarity calculation generating traceable evidence flags for faculty review (never auto-punishing students).
- **AI-Assisted Draft Grading:** Google Gemini-powered criterion evaluation with feedback justifications and late-policy deductions.
- **Governed Grade Publishing:** Multi-state publishing pipeline (`DRAFT` $\to$ `PENDING` $\to$ `APPROVED/REJECTED` $\to$ `PUBLISHED`) with full rollback capabilities.
- **Course Projects & GitHub Review:** Student team repository linking, sprint milestone tracking, health metrics, and faculty review comments.
- **Enterprise FastMCP Server:** Standardized Model Context Protocol server exposing tools and custom URIs (`notes://`, `rubric://`, `assignment://`, `milestones://`).
- **Complete Audit Trail:** Traceable audit logging recording every agent action, input, and output with automated PII and credential redaction.

---

## 5. Seven-Agent Architecture

The core production system is driven by **Seven Specialized Agents** registered in `backend/agents/registry.py`:

```
                          ┌───────────────────────────┐
                          │     AURA Orchestrator     │ (ID: 1)
                          │  (Central LangGraph Sup.) │
                          └─────────────┬─────────────┘
          ┌─────────────────┬───────────┴───────────┬─────────────────┐
          ▼                 ▼                       ▼                 ▼
┌──────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
│ Notes & Knowledge│ │  Assignment &  │ │  Submission &  │ │   Similarity &   │
│      Agent       │ │  Distribution  │ │   Collection   │ │Academic Integrity│
│     (ID: 2)      │ │    (ID: 3)     │ │    (ID: 4)     │ │     (ID: 5)      │
└──────────────────┘ └────────────────┘ └────────────────┘ └──────────────────┘
                            │                       │
                            ▼                       ▼
                   ┌────────────────┐      ┌────────────────┐
                   │   Grading &    │      │   Project &    │
                   │ Feedback Agent │      │Milestone Agent │
                   │    (ID: 6)     │      │    (ID: 7)     │
                   └────────────────┘      └────────────────┘
```

1. **AURAOrchestrator (ID: 1):** Central supervisor managing StateGraph execution, agent routing, checkpointing, and faculty gates.
2. **NotesKnowledgeAgent (ID: 2):** Document parsing (PDF/DOCX), unit organization, version ancestry, and semantic vector retrieval.
3. **AssignmentDistributionAgent (ID: 3):** Brief creation, rubric validation, schedule management, and release dispatching.
4. **SubmissionCollectionAgent (ID: 4):** Intake validation, server timestamping, late delta computation, and SHA-256 checksums.
5. **SimilarityIntegrityAgent (ID: 5):** Pairwise TF-IDF cosine similarity calculations generating traceable evidence records.
6. **GradingFeedbackAgent (ID: 6):** Rubric-grounded draft evaluations and actionable feedback generated via Google Gemini structured outputs.
7. **ProjectMilestoneAgent (ID: 7):** Team project tracking, GitHub repository inspection, checkpoint deliverables, and health metrics.

---

## 6. Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, TanStack Query, Axios, Recharts |
| **Backend API** | FastAPI 0.115, Python 3.12 / 3.13, Uvicorn, Pydantic v2, Pydantic-Settings |
| **Agentic Frameworks** | LangGraph 0.2, LangChain Core, Custom Coordinator-Worker Swarm, ReAct Loop |
| **Protocols & Standards** | Model Context Protocol (FastMCP 1.0+), Streamable HTTP Transport, SSE |
| **LLM & Embeddings** | Google Gemini 2.5 Flash, Gemini 3.1 Flash-Lite, `text-embedding-004` (768-dim) |
| **Data & Storage** | SQLAlchemy 2.0, Alembic, SQLite (aiosqlite), PostgreSQL 16 + pgvector, MinIO / S3 |
| **Document Processing** | PyMuPDF (fitz), python-docx, Scikit-learn (TF-IDF vectorizer), NumPy |
| **DevOps & Containers** | Docker, Docker Compose, Nginx, Pytest, Pytest-Asyncio |

---

## 7. System Architecture

```mermaid
flowchart TD
    subgraph Client Layer
        WebPortal[React + TypeScript Academic Portal]
        Workbench[15-Lab Curriculum Workbench]
    end

    subgraph API & Gateway Layer
        Gateway[FastAPI REST Gateway :8000]
        Auth[JWT Role-Based Access Control]
    end

    subgraph Agentic Orchestration Layer
        Orchestrator[AURA Orchestrator & Supervisor]
        LangGraph[9-Node Cyclic StateGraph Engine]
        Swarm[Parallel Worker Swarm : Semaphore 4]
    end

    subgraph Specialist Agents Layer
        NotesAgent[Notes & Knowledge Agent]
        DistAgent[Assignment & Distribution Agent]
        IntakeAgent[Submission & Collection Agent]
        SimAgent[Similarity & Plagiarism Agent]
        GradeAgent[Grading & Feedback Agent]
        ProjectAgent[Project & Milestone Agent]
    end

    subgraph FastMCP & Protocol Layer
        MCPServer[FastMCP Standalone Server :8001]
        MCPConnector[MCP Client Connector Client]
    end

    subgraph Data & Storage Layer
        DB[(Relational DB : SQLite / PostgreSQL)]
        VectorStore[(Document Chunk Embeddings : 768-dim)]
        FileStore[(Local Storage / MinIO S3)]
        AuditStore[(Immutable Audit Logs)]
    end

    subgraph Governance & Safety
        ApprovalGate{Faculty Approval Gate}
        HumanReview([Named Faculty Member Sign-Off])
    end

    Client Layer <==> Gateway
    Gateway --> Auth
    Auth --> Orchestrator
    Orchestrator <--> LangGraph
    Orchestrator <--> Swarm
    Orchestrator <--> Specialist Agents Layer
    Specialist Agents Layer <--> MCPConnector
    MCPConnector <--> MCPServer
    MCPServer <--> Data & Storage Layer
    Specialist Agents Layer <--> Data & Storage Layer
    GradeAgent --> ApprovalGate
    ApprovalGate <--> HumanReview
    HumanReview -->|Approved & Signed| DB
```

---

## 8. All 14 Hands-on Labs (Curriculum Progression)

The complete hands-on progression specified by Chapter 2 of the curriculum build-book is implemented and fully documented:

| Lab | Title & Documentation | Curriculum Phase | Objective & Implementation Summary |
|:---:|:---|:---|:---|
| **01** | [**Agent vs Chatbot**](Assignments/Lab-01-Agent-vs-Chatbot/README.md) | Phase A — Foundations | ReAct planning loop (Clarify $\to$ Propose $\to$ Revise $\to$ Lock) for structured syllabus outlines. |
| **02** | [**Tool-Using Agent**](Assignments/Lab-02-Tool-Using-Agent/README.md) | Phase A — Foundations | Deterministic typed tools executing in sandboxed Python for accurate arithmetic and statistics. |
| **03** | [**Reusable Skills**](Assignments/Lab-03-Reusable-Skills/README.md) | Phase A — Foundations | Polymorphic parametric skills reusing lesson-planning schemas across Course 1 and Course 2. |
| **04** | [**Memory & Retrieval**](Assignments/Lab-04-Memory-and-Retrieval/README.md) | Phase A — Foundations | Separation of ephemeral session run-state from persistent course-isolated vector retrieval. |
| **05** | [**MCP-Style Connector**](Assignments/Lab-05-MCP-Connector/README.md) | Phase A — Foundations | FastMCP server exposing tools and resources over standard academic URIs (`notes://`, `rubric://`). |
| **06** | [**Governed Runtime**](Assignments/Lab-06-Governed-Runtime/README.md) | Phase A — Foundations | Controlled execution environment enforcing step budgets, invariant contracts, and audit logs. |
| **07** | [**LangGraph Orchestration**](Assignments/Lab-07-LangGraph-Orchestration/README.md) | Phase B — Orchestration | 9-node cyclic StateGraph with self-healing retry back-edge and human-in-the-loop Faculty Gate. |
| **08** | [**Parallel Swarm**](Assignments/Lab-08-Parallel-Swarm/README.md) | Phase B — Orchestration | Multi-agent worker swarm with bounded concurrency (`asyncio.Semaphore(4)`) and aggregation. |
| **09** | [**Deep Research & Grounding**](Assignments/Lab-09-Deep-Research-and-Grounding/README.md) | Phase C — Reliability | Evidence-grounded evaluation extracting verifiable citations and flagging out-of-scope items. |
| **10** | [**Operational Resilience**](Assignments/Lab-10-Operational-Resilience/README.md) | Phase C — Reliability | Autonomous fault diagnosis, jittered exponential backoff, circuit breaking, and error triage. |
| **11** | [**SDLC Factory**](Assignments/Lab-11-SDLC-Factory/README.md) | Phase C — Reliability | Cohort sharding, dual-evaluator consensus scoring, and outlier discrepancy reconciliation. |
| **12** | [**Safety & Governance**](Assignments/Lab-12-Safety-and-Governance/README.md) | Phase D — Governance | Role-based access control (RBAC), student privacy isolation, approval gates, and atomic rollback. |
| **13** | [**Domain Specialists**](Assignments/Lab-13-Domain-Specialists/README.md) | Phase D — Governance | Specialized discipline evaluators for CS (AST/PEP-8), EE (circuits), Biotechnology, and Theory. |
| **14** | [**Integrated Capstone**](Assignments/Lab-14-Integrated-Capstone/README.md) | Phase D — Governance | Complete full-lifecycle system uniting all 7 agents, FastMCP, LangGraph, Swarm, and web portal. |

### Project Extension: Lab 15 (Examiner Live Defense)
- **Title:** Examiner Live Defense & Adversarial Benchmarks
- **Location:** Preserved in canonical source code at [`Course Project/Source Code/backend/lab15_demo.py`](Course%20Project/Source%20Code/backend/lab15_demo.py) and [`Course Project/Source Code/backend/tests/test_lab15.py`](Course%20Project/Source%20Code/backend/tests/test_lab15.py).
- **Description:** Features adversarial prompt-injection defense, automated jailbreak resistance tests, stress load benchmarking, and cryptographic SHA-256 audit sealing.
- **Status:** Fully passing (11/11 tests passed). Included as an advanced project extension.

---

## 9. Installation and Setup

### 9.1 Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ and npm
- Git

### 9.2 Local Installation & Execution

```bash
# 1. Clone the repository
git clone <repository-url>
cd course-project-notes-assignment-organizer

# 2. Setup and Run Backend
cd "Course Project/Source Code/backend"
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env

# Start Backend Server (Port 8000)
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 3. Setup and Run Frontend (in a separate terminal)
cd "Course Project/Source Code/frontend"
npm install
npm run dev
# The web app is now available at http://localhost:5173
```

### 9.3 Standalone FastMCP Server Execution

```bash
cd "Course Project/Source Code/backend"
python -m mcp_server.course_mcp_server --transport streamable-http --port 8001
```

### 9.4 Full Docker Deployment

```bash
cd "Course Project/Source Code"
docker-compose up --build -d
```

---

## 10. Testing and Verification Results

All 15 laboratory demonstration suites pass with a **100% success rate**:

```
============================= test session starts =============================
Platform: Windows, Python 3.13.9, pytest-8.4.2
Rootdir:  Course Project/Source Code/backend
Result:   154 passed, 0 failures, 0 errors in 17.37s
```

| Test Suite | Capability Tested | Tests | Status |
|:---|:---|:---:|:---:|
| `test_lab1.py` | ReAct Planning Loop | 4 | ✅ 4/4 PASS |
| `test_lab2.py` | Typed Tools & Sandboxed Arithmetic | 6 | ✅ 6/6 PASS |
| `test_lab3.py` | Polymorphic Reusable Parametric Skills | 1 | ✅ 1/1 PASS |
| `test_lab4.py` | Dual-Memory Context Store | 4 | ✅ 4/4 PASS |
| `test_lab5.py` | FastMCP Server, Tools & URIs | 5 | ✅ 5/5 PASS |
| `test_lab6.py` | Governed Runtime & Step Budgets | 4 | ✅ 4/4 PASS |
| `test_lab7.py` | LangGraph 9-Node Cyclic StateGraph | 19 | ✅ 19/19 PASS |
| `test_lab8.py` | Multi-Agent Swarm with Bounded Concurrency | 15 | ✅ 15/15 PASS |
| `test_lab9.py` | Deep Research & Citation Grounding | 6 | ✅ 6/6 PASS |
| `test_lab10.py` | Ops Resilience & Self-Healing Diagnostics | 9 | ✅ 9/9 PASS |
| `test_lab11.py` | Swarm Consensus & Cross-Verification | 6 | ✅ 6/6 PASS |
| `test_lab12.py` | Safety, RBAC, and Governed Rollback | 12 | ✅ 12/12 PASS |
| `test_lab13.py` | Discipline Domain Specialists | 11 | ✅ 11/11 PASS |
| `test_lab14.py` | Integrated Production Capstone Pipeline | 41 | ✅ 41/41 PASS |
| `test_lab15.py` | Stress Benchmarks & Adversarial Defense | 11 | ✅ 11/11 PASS |
| **TOTAL** | **Full System Suite** | **154** | ✅ **154/154 PASS (100%)** |

---

## 11. Project Documentation Links

- **Course Project Technical Guide:** [`Course Project/README.md`](Course%20Project/README.md)
- **Assignments Documentation Index:** [`Assignments/README.md`](Assignments/README.md)
- **Original Problem Statement:** [`Course Project/Problem Statement/Original_Worklet_Build_Book.docx`](Course%20Project/Problem%20Statement/Original_Worklet_Build_Book.docx)
- **Chapter 2 Problem Statement Extract:** [`Course Project/Problem Statement/Chapter_2_Course_Project_Problem_Statement.docx`](Course%20Project/Problem%20Statement/Chapter_2_Course_Project_Problem_Statement.docx)
- **Final Course Project Report (DOCX):** [`Course Project/Final Report/AURA_Final_Course_Project_Report.docx`](Course%20Project/Final%20Report/AURA_Final_Course_Project_Report.docx)
- **Final Course Project Report (PDF):** [`Course Project/Final Report/AURA_Final_Course_Project_Report.pdf`](Course%20Project/Final%20Report/AURA_Final_Course_Project_Report.pdf)
- **GitHub Submission & Ownership Transfer Guide:** [`GITHUB_SUBMISSION_AND_OWNERSHIP_GUIDE.md`](GITHUB_SUBMISSION_AND_OWNERSHIP_GUIDE.md)
- **Professor's Submission Form Details:** [`SUBMISSION_FORM_DETAILS.md`](SUBMISSION_FORM_DETAILS.md)

---

## 12. Repository Structure

```
course-project-notes-assignment-organizer/
│
├── Assignments/                               # All 14 hands-on curriculum labs
│   ├── Lab-01-Agent-vs-Chatbot/
│   ├── Lab-02-Tool-Using-Agent/
│   ├── Lab-03-Reusable-Skills/
│   ├── Lab-04-Memory-and-Retrieval/
│   ├── Lab-05-MCP-Connector/
│   ├── Lab-06-Governed-Runtime/
│   ├── Lab-07-LangGraph-Orchestration/
│   ├── Lab-08-Parallel-Swarm/
│   ├── Lab-09-Deep-Research-and-Grounding/
│   ├── Lab-10-Operational-Resilience/
│   ├── Lab-11-SDLC-Factory/
│   ├── Lab-12-Safety-and-Governance/
│   ├── Lab-13-Domain-Specialists/
│   ├── Lab-14-Integrated-Capstone/
│   └── README.md                              # Master assignments index
│
├── Course Project/                            # Production academic platform
│   ├── Source Code/
│   │   ├── backend/                           # FastAPI server, agents & tests
│   │   ├── frontend/                          # React + TypeScript single-page app
│   │   ├── data/                              # Sample database and uploads
│   │   ├── docker-compose.yml                 # Multi-container orchestration
│   │   ├── .env.example                       # Environment configuration template
│   │   └── .gitignore                         # Build and cache exclusion rules
│   │
│   ├── Problem Statement/                     # Official curriculum specifications
│   │   ├── Original_Worklet_Build_Book.docx   # Complete original 15-worklet reference
│   │   └── Chapter_2_Course_Project_Problem_Statement.docx # Chapter 2 extract
│   │
│   ├── Final Report/                          # Comprehensive academic reports
│   │   ├── AURA_Final_Course_Project_Report.docx
│   │   └── AURA_Final_Course_Project_Report.pdf
│   │
│   └── README.md                              # Detailed course project guide
│
├── README.md                                  # Root documentation (this document)
├── LICENSE                                    # MIT Open-Source License
├── .gitignore                                 # Repository-wide clean exclusion rules
├── GITHUB_SUBMISSION_AND_OWNERSHIP_GUIDE.md   # Step-by-step organization transfer guide
└── SUBMISSION_FORM_DETAILS.md                 # Approval form entry verification sheet
```

---

## 13. Future Scope

- **Multi-Modal Visual Grading:** Direct evaluation of handwritten mathematical proofs, circuit schematics, and UI mockups using Gemini Vision.
- **Enterprise LTI 1.3 Integration:** Direct bidirectional gradebook and enrollment synchronization with Canvas, Moodle, and Blackboard.
- **Live Sandboxed Code Execution:** Automatic test runner execution against student GitHub repositories inside isolated Docker microVMs.
- **Audio Lecture Transcription:** Automatic speech-to-text transcription converting recorded lectures into indexed syllabus notes chunks.

---

## 14. Team & Academic Credits

**Team Number:** 14  
**Division:** B  
**Department of Computer Science & Engineering**  
**Course:** Agentic AI (`26ECAC401`) — Semester 7, 2026  

- **Amrutavarshini B** (`01FE23BCI024`)
- **Pooja Pattar** (`01FE23BCI058`)
- **Vaishnavi Pagad** (`01FE23BCI063`)
- **Vaishnavi Kudlamath** (`01FE23BCI012`)

*Faculty Guide & Course Instructor: Dr. Uday Kulkarni*
