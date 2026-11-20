# Course Project: apniLeap AURA (Academic Utility & Resilience Agent)

**Artifact Name:** Chapter 2. Course Project, Notes & Assignment Organizer  
**Team Number:** 14 | **Division:** B  
**Academic Year:** 2026 | **Course:** Agentic AI (26ECAC401)  

---

## 1. Project Overview

**apniLeap AURA** is an enterprise-grade multi-agent academic operations platform and pedagogical workbench. It was developed to solve the core challenges of modern university course management: fragmented note sharing across channels, manual assignment collection, rubric evaluation inconsistencies, grading fatigue, unverified plagiarism claims, and unmonitored capstone team milestones.

AURA consolidates these operations into three synchronized functional streams governed by autonomous specialist agents:
1. **Versioned Notes & Knowledge Repository:** Automated parsing (PDF/DOCX), unit/topic categorization, document version lineage tracking, and 768-dimensional vector retrieval.
2. **Assignment Distribution & Governed Grading:** Structured criteria rubrics, authoritative deadline timestamping, SHA-256 integrity checks, pairwise TF-IDF plagiarism detection, Google Gemini AI draft grading, and an immutable Faculty Approval Gate.
3. **Capstone Project & Milestone Tracking:** Student team management, GitHub repository commit tracking, checkpoint health indicators (green/amber/red), and faculty codebase review.

---

## 2. Core Invariant: Human-in-the-Loop Authority

> **"Agents draft, cross-check, diagnose, and flag; a named human faculty member inspects, overrides, and approves."**

Under no circumstances does an autonomous agent publish grades, distribute finalized materials, or penalize students without explicit instructor review and approval.

---

## 3. Seven Core Production Specialists

Formally registered in `backend/agents/registry.py` and accessible via `GET /agents/`:

| Agent ID | Specialist Agent | Core Responsibility | Runtime Model |
|:---:|:---|:---|:---|
| **1** | **AURAOrchestrator** | Supervisor coordinating multi-agent routing, StateGraph lifecycle, and human approval gates. | LangGraph Supervisor |
| **2** | **NotesKnowledgeAgent** | Ingests lecture notes, manages version lineages, and handles course-scoped semantic RAG. | Deterministic RAG |
| **3** | **AssignmentDistributionAgent** | Generates assignment briefs, validates rubric totals, and manages release schedules. | Deterministic Service |
| **4** | **SubmissionCollectionAgent** | Handles student uploads, validates file types, and computes SHA-256 tamper-detection hashes. | Deterministic Storage |
| **5** | **SimilarityIntegrityAgent** | Pairwise TF-IDF similarity calculation producing traceable overlap flags for faculty review. | Hybrid TF-IDF / Vector |
| **6** | **GradingFeedbackAgent** | AI-assisted rubric evaluation and feedback drafting using Google Gemini structured outputs. | Gemini Structured LLM |
| **7** | **ProjectMilestoneAgent** | Monitors semester team projects, GitHub repositories, deliverables, and checkpoint health. | Hybrid Deterministic / LLM |

---

## 4. System Architecture & Workflows

### 4.1 FastMCP Client-Server Infrastructure
AURA implements the Model Context Protocol (FastMCP) in `backend/mcp_server/course_mcp_server.py`:
- **Standardized URIs:** `notes://{course_id}/{unit}`, `rubric://{course_id}/{assignment_id}`, `assignment://{course_id}/{assignment_id}`, and `milestones://{course_id}/{milestone_id}`.
- **Exposed Tools:** `search_course_notes`, `get_note`, `get_assignments`, `validate_assignment`, `get_submission`, `get_pending_approvals`, and `approve_grade`.
- **Transports:** Supports both in-process embedded connector mode and Streamable HTTP on port 8001.

### 4.2 LangGraph 9-Node Cyclic StateGraph
Configured in `backend/agents/node_graph_pipeline.py`:
```
Ingest → Plan → Distribute → Ingest Submissions → Similarity Check → AI Grading → Validate
                                 ▲                                                  │
                                 └─────────── (Retry Back-Edge: attempts < MAX) ────┘
                                                                                    │ (Passed)
                                                                                    ▼
                                          Governed Publish ◄── [Faculty Approval Gate]
```

### 4.3 Parallel Swarm Architecture
Configured in `backend/agents/swarm_pipeline.py`:
- Bounded concurrency governed by `asyncio.Semaphore(4)`.
- Non-blocking batch processing of student cohorts without LLM rate-limit exhaustion.
- Automatic result aggregation computing average score, median, standard deviation, and flag tallies.

---

## 5. Source Code Organization

The complete source code is organized under `Course Project/Source Code/`:

```
Course Project/Source Code/
├── backend/
│   ├── agents/           # Seven specialist agents & swarm pipelines
│   ├── alembic/          # Alembic database migration scripts
│   ├── api/              # FastAPI application and route controllers
│   ├── connector/        # FastMCP client connector
│   ├── mcp_server/       # FastMCP standalone server implementation
│   ├── migrations/       # SQLite to PostgreSQL migration scripts
│   ├── models/           # SQLAlchemy 2.0 ORM schemas
│   ├── runtime/          # Governance engine, audit logger, and capstone
│   ├── services/         # Modular business services layer
│   ├── skills/           # Polymorphic parametric course skills
│   ├── tests/            # Pytest test suites (Labs 1 through 15)
│   ├── tools/            # Deterministic typed tools & sandbox
│   ├── validation/       # Pydantic v2 rubric validators
│   ├── Dockerfile        # Backend production container specification
│   ├── config.py         # Environment-based configuration
│   └── requirements.txt  # Python dependency specifications
│
├── frontend/
│   ├── src/
│   │   ├── components/   # Layout, navigation, and feedback modals
│   │   ├── pages/        # Dashboard, Notes, Assignments, Grades, Milestones, Labs
│   │   ├── services/     # Axios API client functions
│   │   └── App.tsx       # Route definitions and authentication guards
│   ├── Dockerfile        # Multi-stage frontend container (Node.js + Nginx)
│   ├── nginx.conf        # Production Nginx reverse-proxy configuration
│   └── package.json      # React 18 & TypeScript dependencies
│
├── data/                 # Sample SQLite database and storage mounts
├── docker-compose.yml    # Full-stack container orchestration
└── .env.example          # Environment variable template
```

---

## 6. Installation & Execution

### 6.1 Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### 6.2 Running Locally

```bash
# 1. Backend Setup
cd "Course Project/Source Code/backend"
python -m venv venv
# On Windows: venv\Scripts\activate | On Unix: source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env

# Launch Backend Server (Port 8000)
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 2. Frontend Setup (in a separate terminal)
cd "Course Project/Source Code/frontend"
npm install
npm run dev
# Web application will be live at http://localhost:5173
```

### 6.3 Running with Docker Compose

```bash
cd "Course Project/Source Code"
docker-compose up --build -d
```

---

## 7. Automated Testing & Verification

AURA features a comprehensive test suite covering all 15 curriculum laboratories.

```bash
cd "Course Project/Source Code/backend"
python -m pytest tests/ -v
```

**Verification Results:**
- **Total Tests:** 154
- **Passed:** 154 (100% PASS)
- **Failed:** 0
- **Duration:** 17.37s

---

## 8. Related Deliverables
- **Original Problem Statement:** [`Problem Statement/Original_Worklet_Build_Book.docx`](Problem%20Statement/Original_Worklet_Build_Book.docx)
- **Chapter 2 Extract:** [`Problem Statement/Chapter_2_Course_Project_Problem_Statement.docx`](Problem%20Statement/Chapter_2_Course_Project_Problem_Statement.docx)
- **Final Course Report (DOCX):** [`Final Report/AURA_Final_Course_Project_Report.docx`](Final%20Report/AURA_Final_Course_Project_Report.docx)
- **Final Course Report (PDF):** [`Final Report/AURA_Final_Course_Project_Report.pdf`](Final%20Report/AURA_Final_Course_Project_Report.pdf)
- **Assignments Documentation (Labs 1–14):** [`../Assignments/README.md`](../Assignments/README.md)
