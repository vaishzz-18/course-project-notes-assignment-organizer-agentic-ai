# AURA Laboratory Assignments Index (Labs 01 – 14)

**Artifact:** Chapter 2. Course Project, Notes & Assignment Organizer  
**Team Number:** 14 | **Division:** B  
**Academic Year:** 2026 | **Course:** Agentic AI (26ECAC401)  

---

## Overview

This directory contains the complete technical documentation, architecture specifications, execution procedures, and verification test evidence for all **14 hands-on laboratory assignments** mandated by the curriculum specification:

*Source Reference:* `Agentic_AI_15_Worklets_14Lab_Build_Book.docx` (Chapter 2).

---

## Master Laboratory Index

| Lab | Title & Documentation | Curriculum Phase | Test Status |
|:---:|:---|:---|:---:|
| Lab 01 | [Agent vs Chatbot — Cognitive Planning Loop](Lab-01-Agent-vs-Chatbot/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 02 | [Tool-Using Agent — Typed Tools & Sandboxed Execution](Lab-02-Tool-Using-Agent/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 03 | [Skill Creation — Polymorphic Parametric Skills](Lab-03-Reusable-Skills/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 04 | [Context & Memory — Short-Term State & Semantic Store](Lab-04-Memory-and-Retrieval/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 05 | [Model Context Protocol — FastMCP Connector & Resources](Lab-05-MCP-Connector/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 06 | [Governed Runtime — Step Budgets & Invariant Enforcement](Lab-06-Governed-Runtime/README.md) | Phase A — Foundations | ✅ Verified PASS |
| Lab 07 | [LangGraph Orchestration — 9-Node Cyclic StateGraph](Lab-07-LangGraph-Orchestration/README.md) | Phase B — Orchestration | ✅ Verified PASS |
| Lab 08 | [Parallel Swarm — Bounded Concurrency & Aggregation](Lab-08-Parallel-Swarm/README.md) | Phase B — Orchestration | ✅ Verified PASS |
| Lab 09 | [Deep Research & Grounding — Verifiable Citations](Lab-09-Deep-Research-and-Grounding/README.md) | Phase C — Applied Reliability | ✅ Verified PASS |
| Lab 10 | [Operational Resilience — Self-Healing & Diagnostics](Lab-10-Operational-Resilience/README.md) | Phase C — Applied Reliability | ✅ Verified PASS |
| Lab 11 | [SDLC Factory — Consensus Sharding & Cross-Verification](Lab-11-SDLC-Factory/README.md) | Phase C — Applied Reliability | ✅ Verified PASS |
| Lab 12 | [Safety & Governance — RBAC, Privacy & Governed Rollback](Lab-12-Safety-and-Governance/README.md) | Phase D — Governance and Capstone | ✅ Verified PASS |
| Lab 13 | [Domain Specialists — Multi-Discipline Evaluation](Lab-13-Domain-Specialists/README.md) | Phase D — Governance and Capstone | ✅ Verified PASS |
| Lab 14 | [Integrated Capstone — Full AURA System](Lab-14-Integrated-Capstone/README.md) | Phase D — Governance and Capstone | ✅ Verified PASS |

---

## Capstone Extension: Lab 15 (Examiner Live Defense)
- **Title:** Examiner Live Defense & Adversarial Benchmarks
- **Location:** Preserved in canonical source code at [`backend/lab15_demo.py`](../Course%20Project/Source%20Code/backend/lab15_demo.py) and [`backend/tests/test_lab15.py`](../Course%20Project/Source%20Code/backend/tests/test_lab15.py).
- **Description:** Features adversarial prompt-injection defense, automated jailbreak resistance tests, stress load benchmarking, and cryptographic SHA-256 audit sealing.
- **Classification:** Documented as a project extension beyond the 14 core syllabus assignments.

---

## Verification Summary
Every laboratory implementation is verified through dedicated automated tests in `backend/tests/`. All 154 test cases across the entire platform pass with a **100% success rate**.
