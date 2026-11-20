"""
Seed Rich Data script:
Populates Classroom with a full, realistic academic ecosystem.
- Faculty: Dr. Uday Kulkarni (uday.kulkarni@classroom.edu / faculty@classroom.edu)
- Courses under Dr. Uday Kulkarni:
  1. Agentic AI (CS401)
  2. Generative AI (CS402)
  3. Machine Learning (CS301)
- Other courses & faculty:
  4. Distributed Systems & Cloud Infrastructure (CS302) — Prof. Rajesh Raman
  5. Deep Learning & Neural Architectures (CS405) — Dr. Vaishnavi Patel
  6. Data Structures & Algorithmic Analysis (CS201) — Prof. Arvind Swaminathan
- 18+ Students enrolled across multiple courses
- Real-world Notes with multi-version histories (v1, v2, v3)
- Comprehensive Assignments with 100-mark rubrics
- Student Submissions with code bodies (on-time, late-penalized, plagiarism pairs)
- Realistic Grades (drafts, pending approval, approved, published)
- Course Project Groups with linked GitHub repository URLs and checkpoint milestones
- All accounts use password: aura@1010
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select, delete, text
from passlib.context import CryptContext
from models.database import (
    Base, engine, AsyncSessionLocal, User, UserRole, Course, CourseEnrollment,
    Note, Assignment, AssignmentStatus, Submission, Grade, GradeStatus,
    ProjectGroup, GroupMember, Milestone, MilestoneProgress, MilestoneProgressStatus,
    MilestoneHealth, AuditLog
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PWD_HASH = pwd_context.hash("aura@1010")


async def seed_rich_data():
    print("=" * 75)
    print("CLASSROOM ACADEMIC DATASET SEEDER")
    print("=" * 75)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Clean existing records for a fresh, consistent academic catalog
        print("\n[1/7] Refreshing database tables for clean academic state...")
        await session.execute(delete(AuditLog))
        await session.execute(delete(MilestoneProgress))
        await session.execute(delete(Milestone))
        await session.execute(delete(GroupMember))
        await session.execute(delete(ProjectGroup))
        await session.execute(delete(Grade))
        await session.execute(delete(Submission))
        await session.execute(delete(Assignment))
        await session.execute(delete(Note))
        await session.execute(delete(CourseEnrollment))
        await session.execute(delete(Course))
        await session.execute(delete(User))
        try:
            await session.execute(text("DELETE FROM sqlite_sequence"))
        except Exception:
            pass
        await session.commit()

        # 2. Seed Faculty and Students (No HoD account!)
        print("[2/7] Seeding Faculty & Students cohort (Password: aura@1010)...")
        faculty_users = [
            # Dr. Uday Kulkarni (Primary Faculty Lead)
            User(name="Dr. Uday Kulkarni", email="uday.kulkarni@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Dr. Uday Kulkarni", email="faculty@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Dr. Uday Kulkarni", email="faculty@aura.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            # Other departmental faculty
            User(name="Prof. Rajesh Raman", email="rajesh@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Prof. Rajesh Raman", email="raman@aura.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Dr. Vaishnavi Patel", email="vaishnavi@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Dr. Pooja Sharma", email="pooja@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
            User(name="Prof. Arvind Swaminathan", email="arvind@classroom.edu", password_hash=DEFAULT_PWD_HASH, role=UserRole.faculty),
        ]
        session.add_all(faculty_users)
        await session.flush()

        dr_uday = faculty_users[0]
        prof_raman = faculty_users[3]
        dr_vaishnavi = faculty_users[5]
        dr_pooja = faculty_users[6]
        prof_arvind = faculty_users[7]

        students_data = [
            ("Alex Chen", "alex@classroom.edu"),
            ("Priya Sharma", "priya@classroom.edu"),
            ("Marcus Vance", "marcus@classroom.edu"),
            ("Elena Rostova", "elena@classroom.edu"),
            ("David Kim", "david@classroom.edu"),
            ("Emily Zhang", "emily@classroom.edu"),
            ("Liam O'Connor", "liam@classroom.edu"),
            ("Sophia Martinez", "sophia@classroom.edu"),
            ("Tariq Al-Mansoor", "tariq@classroom.edu"),
            ("Chloe Dubois", "chloe@classroom.edu"),
            ("Vikram Malhotra", "vikram@classroom.edu"),
            ("Zoe Washington", "zoe@classroom.edu"),
            ("Carlos Mendez", "carlos@classroom.edu"),
            ("Ananya Roy", "ananya@classroom.edu"),
            ("Kevin Zhang", "kevin@classroom.edu"),
            ("Sarah Jenkins", "sarah@classroom.edu"),
            ("Ethan Hunt", "ethan@classroom.edu"),
            ("Mei Lin", "mei@classroom.edu"),
            # Compatibility aliases
            ("Alex Chen", "alex@aura.edu"),
            ("Priya Sharma", "priya@aura.edu"),
            ("Marcus Vance", "marcus@aura.edu"),
            ("Elena Rostova", "elena@aura.edu"),
            ("David Kim", "david@aura.edu"),
            ("Demo Student", "student@classroom.edu"),
            ("Demo Student", "student@aura.edu"),
        ]

        student_users = [
            User(name=name, email=email, password_hash=DEFAULT_PWD_HASH, role=UserRole.student)
            for name, email in students_data
        ]
        session.add_all(student_users)
        await session.flush()
        print(f"  -> Created Faculty & {len(student_users)} Student accounts.")

        # 3. Seed Courses (3 under Dr. Uday Kulkarni, plus other disciplines)
        print("\n[3/7] Seeding Academic Courses under Dr. Uday Kulkarni & Faculty...")
        courses = [
            # 1. Agentic AI (CS401) — Dr. Uday Kulkarni
            Course(
                name="Agentic AI & Autonomous Systems",
                code="CS401",
                description="Advanced engineering of ReAct cognitive loops, MCP protocol connectors, LangGraph state-graphs, parallel swarms, and human-in-the-loop safety governance.",
                faculty_id=dr_uday.id
            ),
            # 2. Generative AI (CS402) — Dr. Uday Kulkarni
            Course(
                name="Generative AI & Large Language Models",
                code="CS402",
                description="Comprehensive study of Diffusion models, LLM Alignment (RLHF/DPO), Vector Embeddings, RAG Architectures, and Multimodal Transformers.",
                faculty_id=dr_uday.id
            ),
            # 3. Machine Learning (CS301) — Dr. Uday Kulkarni
            Course(
                name="Machine Learning & Statistical Foundations",
                code="CS301",
                description="Supervised & unsupervised learning algorithms, convex optimization, ensemble gradient boosting, cross-validation, and model fairness.",
                faculty_id=dr_uday.id
            ),
            # 4. Distributed Systems (CS302) — Prof. Rajesh Raman
            Course(
                name="Distributed Systems & Cloud Infrastructure",
                code="CS302",
                description="Architectures for high-throughput distributed systems, Raft consensus, vector clocks, and fault-tolerant microservices.",
                faculty_id=prof_raman.id
            ),
            # 5. Deep Learning (CS405) — Dr. Vaishnavi Patel
            Course(
                name="Deep Learning & Neural Architectures",
                code="CS405",
                description="Transformer attention mechanisms, vision-language models, diffusion generative processes, and self-supervised learning systems.",
                faculty_id=dr_vaishnavi.id
            ),
            # 6. Data Structures (CS201) — Prof. Arvind Swaminathan
            Course(
                name="Data Structures & Algorithmic Analysis",
                code="CS201",
                description="Rigorous algorithmic analysis, balanced trees, graph flow networks, dynamic programming, and NP-hard problem approximations.",
                faculty_id=prof_arvind.id
            ),
        ]
        session.add_all(courses)
        await session.flush()

        # Enroll students across courses (students enrolled in multiple courses)
        enrollments = []
        for c_idx, course in enumerate(courses):
            # Agentic AI, Generative AI, and Machine Learning get all students; others get subsets
            assigned = student_users if c_idx < 3 else student_users[:14]
            for s in assigned:
                enrollments.append(CourseEnrollment(course_id=course.id, student_id=s.id))
        session.add_all(enrollments)
        await session.flush()
        print(f"  -> Seeded {len(courses)} Courses with {len(enrollments)} active enrollments.")

        # 4. Seed Notes Repository with Multi-Version History
        print("\n[4/7] Seeding Notes Repository with Multi-Version Histories (v1, v2, v3)...")
        notes_dir = Path(__file__).parent.parent / "data" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        notes_to_seed = [
            # CS401 Notes (Dr. Uday Kulkarni) — Preserving exact unit tags & versioning for test suite assertions
            (courses[0], "Lecture 1: Foundations of Agentic AI", "Unit 1", "Agent Architecture", [
                ("v1", "Unit 1: Agentic Foundations (v1)\nAgent definition: Perception, Reasoning, Action loop. Agent vs Chatbot distinction."),
                ("v2", "Unit 1: Agentic Foundations (v2 Updated)\nExpanded coverage on ReAct cognitive cycles, prompt decomposition, and stopping conditions."),
            ]),
            (courses[0], "Lecture 2: MCP & Typed Tool Execution", "Unit 2", "MCP Protocol", [
                ("v1", "Unit 2: Tools & Model Context Protocol (MCP)\nDecoupling data access from agent logic using standard JSON-RPC MCP servers."),
            ]),
            (courses[0], "Lecture 3: LangGraph Orchestration", "Unit 3", "State Graphs", [
                ("v1", "Unit 3: LangGraph StateGraphs\nState management, conditional routing, human-in-the-loop review nodes, and retry back-edges."),
            ]),
            (courses[0], "Lecture 4: Parallel Swarm & Fan-Out/Fan-In", "Unit 4", "Async Worker Pools", [
                ("v1", "Asynchronous worker pool processing concurrent submission grading with plan-aligned fan-in draft synthesis."),
            ]),
            (courses[0], "Lecture 5: Safety, Reliability & Rollback", "Unit 5", "Release Engineering", [
                ("v1", "Formal faculty approval gate, role-based confidentiality filters, versioned releases, and 1-click rollback restoration."),
            ]),

            # CS402 Notes (Generative AI — Dr. Uday Kulkarni)
            (courses[1], "Lecture 1: Diffusion Probabilistic Models", "Unit 1", "Latent Diffusion & Score Matching", [
                ("v1", "Forward and reverse diffusion Markov chains, noise schedules, score matching, and classifier-free guidance."),
                ("v2", "Latent Diffusion Models (LDM): VAE latent compression space, cross-attention conditioning, and SDXL architecture."),
            ]),
            (courses[1], "Lecture 2: LLM Post-Training Alignment (RLHF & DPO)", "Unit 2", "Preference Optimization", [
                ("v1", "Reward modeling from pairwise comparisons, PPO policy optimization with KL penalty constraint."),
                ("v2", "Direct Preference Optimization (DPO): Eliminating the reward model via direct implicit reward derivation."),
            ]),
            (courses[1], "Lecture 3: Production RAG & Hybrid Vector Search", "Unit 3", "Retrieval Systems", [
                ("v1", "Dense vector embeddings, approximate nearest neighbors (HNSW), sparse BM25 fusion, and cross-encoder reranking."),
            ]),
            (courses[1], "Lecture 4: Multimodal Vision-Language Transformers", "Unit 4", "Multimodal Fusion", [
                ("v1", "Contrastive Language-Image Pre-training (CLIP), vision projection layers, and autoregressive visual generation."),
            ]),

            # CS301 Notes (Machine Learning — Dr. Uday Kulkarni)
            (courses[2], "Lecture 1: Supervised Learning & Convex Loss", "Unit 1", "Linear & Logistic Models", [
                ("v1", "Empirical Risk Minimization (ERM), L1/L2 regularization, batch gradient descent, and Newton-Raphson methods."),
                ("v2", "Stochastic Gradient Descent (SGD): Momentum, AdaGrad, Adam optimizer, learning rate schedules, and convergence bounds."),
            ]),
            (courses[2], "Lecture 2: Decision Trees & Gradient Boosting Ensembles", "Unit 2", "Ensemble Methods", [
                ("v1", "Information gain, Gini impurity, bagging, Random Forests, out-of-bag error estimation."),
                ("v2", "Gradient Boosted Decision Trees (GBDT): XGBoost split-finding algorithms, LightGBM histogram binning, and CatBoost categorical encoding."),
            ]),
            (courses[2], "Lecture 3: Unsupervised Representation & Clustering", "Unit 3", "Clustering & PCA", [
                ("v1", "K-Means convergence proofs, Spectral Clustering, Principal Component Analysis (PCA) SVD decomposition, and t-SNE embeddings."),
            ]),

            # CS302 Notes (Distributed Systems — Prof. Rajesh Raman)
            (courses[3], "Lecture 1: RPC Systems & gRPC Protocols", "Unit 1", "Remote Invocations", [
                ("v1", "Principles of RPC semantics, protocol buffer serialization, and streaming network channels."),
            ]),
            (courses[3], "Lecture 2: Raft Consensus & Log Replication", "Unit 2", "Distributed Consensus", [
                ("v1", "Raft state machine replication: leader election, log consistency invariants, and split-brain resolution."),
                ("v2", "Raft state machine replication: added membership reconfiguration and log compaction snapshots."),
            ]),

            # CS405 Notes (Deep Learning — Dr. Vaishnavi Patel)
            (courses[4], "Lecture 1: Multi-Head Attention Mechanisms", "Unit 1", "Scaled Dot-Product", [
                ("v1", "Mathematical formulation of Queries, Keys, and Values. Self-attention complexity and causal masking."),
                ("v2", "Multi-Head Attention: FlashAttention kernel optimizations and RoPE rotary positional encodings."),
            ]),

            # CS201 Notes (Data Structures — Prof. Arvind Swaminathan)
            (courses[5], "Lecture 1: Red-Black Trees & Balanced Search", "Unit 1", "Balanced Trees", [
                ("v1", "Invariants of Red-Black balanced search trees, color flips, rotations, and asymptotic O(log n) worst-case bounds."),
            ]),
        ]

        total_notes_created = 0
        for course, title, unit, topic, versions in notes_to_seed:
            parent_note = None
            for v_idx, (v_tag, text_body) in enumerate(versions):
                ver_num = v_idx + 1
                is_latest = (ver_num == len(versions))
                fn = f"{course.code.lower()}_{unit[:6].lower().replace(' ', '_').replace(':', '')}_v{ver_num}.txt"
                fp = notes_dir / fn
                fp.write_text(f"{title} ({v_tag})\nCourse: {course.name} ({course.code})\nFaculty: {course.faculty_id}\n\n{text_body}")

                note_record = Note(
                    course_id=course.id,
                    title=f"{title} ({v_tag})" if len(versions) > 1 else title,
                    unit=unit,
                    topic=topic,
                    file_path=str(fp),
                    file_name=fn,
                    version=ver_num,
                    is_current=is_latest,
                    parent_id=parent_note.id if parent_note else None,
                    uploaded_by=course.faculty_id
                )
                session.add(note_record)
                await session.flush()
                if ver_num == 1:
                    parent_note = note_record
                total_notes_created += 1

        print(f"  -> Generated {total_notes_created} Note records with multi-version lineage.")

        # 5. Seed Course Assignments with 100-Mark Rubrics
        print("\n[5/7] Seeding Course Assignments with 100-Mark Rubric Specifications...")
        assignments_data = [
            # CS401 Assignments (Dr. Uday Kulkarni)
            (
                courses[0],
                "Assignment 1: Build a Tool-Using ReAct Agent",
                "Design and implement an autonomous ReAct cognitive loop with at least 3 registered tools and bounded retry logic.",
                {
                    "code_correctness": {"max": 40, "description": "Deterministic tool execution and zero LLM arithmetic."},
                    "react_loop_reasoning": {"max": 25, "description": "Thought-Action-Observation trace logged accurately."},
                    "error_handling": {"max": 20, "description": "Targeted self-healing upon tool failure."},
                    "documentation": {"max": 15, "description": "Architecture spec, PEP-8 compliance, and docstrings."}
                },
                timedelta(days=-1),  # Past due (Oct 28, 2026, 11:59 PM) so submissions on Oct 25-28 are on-time, and Oct 30-31 are genuinely late
                AssignmentStatus.published
            ),
            (
                courses[0],
                "Assignment 2: LangGraph StateGraph Orchestrator",
                "Construct a 9-node LangGraph pipeline with a conditional retry back-edge and named human FacultyGate.",
                {
                    "graph_topology": {"max": 35, "description": "Complete 9-node StateGraph compiled correctly."},
                    "retry_backedge": {"max": 25, "description": "Self-healing edge triggered when rubric check fails."},
                    "faculty_gate_stop": {"max": 25, "description": "Execution unconditionally halts until human approves."},
                    "audit_provenance": {"max": 15, "description": "Full step logging via runtime."}
                },
                timedelta(days=14),
                AssignmentStatus.published
            ),
            (
                courses[0],
                "Assignment 3: Parallel Swarm & Evidence Grounding",
                "Implement an asynchronous worker pool fan-out with paper-level evidence table generation.",
                {
                    "parallel_speedup": {"max": 35, "description": "Concurrent execution measurably faster than sequential baseline."},
                    "evidence_grounding": {"max": 35, "description": "Each output carries verified syllabus and rubric citations."},
                    "out_of_scope_reject": {"max": 30, "description": "Zero ungrounded or non-syllabus claims slip through."}
                },
                timedelta(days=28),
                AssignmentStatus.published
            ),

            # CS402 Assignments (Generative AI — Dr. Uday Kulkarni)
            (
                courses[1],
                "Assignment 1: Fine-Tuning with LoRA & DPO Alignment",
                "Implement Parameter-Efficient Fine-Tuning (LoRA) on an open-weight LLM, followed by Direct Preference Optimization (DPO).",
                {
                    "lora_implementation": {"max": 35, "description": "Low-rank adapter injection into query/value weight matrices."},
                    "dpo_loss": {"max": 35, "description": "Implicit reward log-ratio loss computation with reference model freezing."},
                    "evaluation_benchmarks": {"max": 30, "description": "Perplexity and human evaluation win-rate comparison."}
                },
                timedelta(days=10),
                AssignmentStatus.published
            ),
            (
                courses[1],
                "Assignment 2: Production Hybrid RAG Pipeline",
                "Build an enterprise retrieval-augmented generation pipeline with hybrid dense/sparse vector retrieval and cross-encoder reranking.",
                {
                    "hybrid_retrieval": {"max": 40, "description": "Reciprocal Rank Fusion (RRF) between dense embeddings and BM25."},
                    "reranker_integration": {"max": 30, "description": "Cross-encoder scoring and context window compression."},
                    "grounding_check": {"max": 30, "description": "Automated hallucination detection and citation verification."}
                },
                timedelta(days=21),
                AssignmentStatus.published
            ),

            # CS301 Assignments (Machine Learning — Dr. Uday Kulkarni)
            (
                courses[2],
                "Assignment 1: Gradient Descent & Regularized Logistic Regression",
                "Implement vectorized binary logistic regression from scratch with L1/L2 regularization and mini-batch SGD.",
                {
                    "vectorized_gradients": {"max": 40, "description": "Zero Python loops in forward pass and backward gradient computation."},
                    "regularization_math": {"max": 30, "description": "Correct penalty gradients and subgradient handling for L1."},
                    "convergence_plots": {"max": 30, "description": "Loss curves across learning rates and decision boundary plots."}
                },
                timedelta(days=7),
                AssignmentStatus.published
            ),
            (
                courses[2],
                "Assignment 2: Gradient Boosted Trees Ensemble Pipeline",
                "Construct a gradient boosting regressor fitting pseudo-residuals of squared error loss with tree pruning.",
                {
                    "pseudo_residuals": {"max": 35, "description": "Analytical negative gradient calculation at each boosting step."},
                    "tree_pruning": {"max": 35, "description": "Max depth and minimum sample split constraints enforced."},
                    "validation_curves": {"max": 30, "description": "Early stopping based on validation set RMSE."}
                },
                timedelta(days=18),
                AssignmentStatus.published
            ),

            # CS302 Assignments (Prof. Rajesh Raman)
            (
                courses[3],
                "Lab 1: Distributed Key-Value Store with Vector Clocks",
                "Implement a distributed hash table with vector clock causality tracking and read repair.",
                {
                    "causal_ordering": {"max": 40, "description": "Vector clock increments and concurrent conflict detection."},
                    "read_repair": {"max": 30, "description": "Automatic convergence of stale replicas upon read quorum."},
                    "benchmarks": {"max": 30, "description": "Throughput and latency profiling under network jitter."}
                },
                timedelta(days=8),
                AssignmentStatus.published
            ),

            # CS405 Assignments (Dr. Vaishnavi Patel)
            (
                courses[4],
                "Assignment 1: Custom Transformer Block from Scratch",
                "Implement multi-head self-attention with causal masking, layer normalization, and residual additions in PyTorch.",
                {
                    "attention_math": {"max": 45, "description": "Correct QK^T / sqrt(d_k) matrix multiplication and softmax."},
                    "residual_norm": {"max": 30, "description": "Pre-LN vs Post-LN implementation with gradient flow."},
                    "unit_tests": {"max": 25, "description": "Shape verification and numerical gradient assertions."}
                },
                timedelta(days=12),
                AssignmentStatus.published
            ),

            # CS201 Assignments (Prof. Arvind Swaminathan)
            (
                courses[5],
                "Problem Set 1: Graph Network Flow & Bipartite Matching",
                "Implement Ford-Fulkerson with Edmonds-Karp augmenting paths to solve maximum bipartite matching problems.",
                {
                    "flow_correctness": {"max": 50, "description": "Max-flow equals min-cut verification."},
                    "complexity_proof": {"max": 30, "description": "O(V E^2) theoretical complexity bound maintained."},
                    "test_rigor": {"max": 20, "description": "Handles disconnected components, cycles, and capacity constraints."}
                },
                timedelta(days=6),
                AssignmentStatus.published
            ),
        ]

        created_assignments = []
        for course, title, desc, rubric, delta, status in assignments_data:
            a = Assignment(
                course_id=course.id,
                title=title,
                description=desc,
                rubric=json.dumps(rubric),
                max_marks=100.0,
                due_date=datetime.utcnow() + delta,
                status=status,
                created_by=course.faculty_id,
                published_at=datetime.utcnow() - timedelta(days=3)
            )
            session.add(a)
            created_assignments.append(a)
        await session.flush()
        print(f"  -> Created {len(created_assignments)} Assignments across all courses.")

        # 6. Seed Submissions & Grades
        print("\n[6/7] Seeding Student Submissions & Evaluated Grades...")
        sub_dir = Path(__file__).parent.parent / "data" / "submissions"
        sub_dir.mkdir(parents=True, exist_ok=True)

        asgn1 = created_assignments[0]  # CS401 Asgn 1
        asgn1.due_date = datetime(2026, 10, 28, 23, 59, 0)
        await session.flush()

        alex_code = '''# ReAct Agent Implementation by Alex Chen
import json

class ReActAgent:
    def __init__(self, tools):
        self.tools = tools
        self.memory = []

    def reason_and_act(self, query):
        print(f"Thought: Analyzing query '{query}'")
        for tool in self.tools:
            if tool.can_handle(query):
                res = tool.execute(query)
                return f"Final Answer: {res}"
        return "Cannot solve query"
'''
        priya_code = '''# ReAct Tool Agent by Priya Sharma
from typing import Dict, Any

class AgentPipeline:
    def __init__(self):
        self.log = []

    def execute_react_step(self, user_prompt: str) -> Dict[str, Any]:
        # Thought: Check data connector
        # Action: Query notes
        return {"status": "success", "result": "Calculated accurately with tools"}
'''
        marcus_code = '''# ReAct Implementation by Marcus Vance
class ToolExecutor:
    def __init__(self):
        self.history = []

    def run(self, task: str):
        return f"Executed task: {task}"
'''

        student_sub_specs = [
            # 0: Alex Chen - Oct 25, 14:30 (On time, 3 days before deadline)
            (alex_code, datetime(2026, 10, 25, 14, 30), 0.12, [{"with_student": "Elena Rostova", "score": 0.96, "reason": "High similarity with Elena Rostova"}, {"with_student": "David Kim", "score": 0.96, "reason": "High similarity with David Kim"}]),
            # 1: Priya Sharma - Oct 26, 10:15 (On time)
            (priya_code, datetime(2026, 10, 26, 10, 15), 0.15, None),
            # 2: Marcus Vance - Oct 27, 16:00 (On time)
            (marcus_code, datetime(2026, 10, 27, 16, 0), 0.10, None),
            # 3: Elena Rostova - Oct 28, 11:20 (On time, verbatim identical to Alex Chen)
            (alex_code.replace("Alex Chen", "Elena Rostova"), datetime(2026, 10, 28, 11, 20), 0.96, [{"with_student": "Alex Chen", "student_id": student_users[0].id, "score": 0.96, "percentage": "96%", "reason": "Verbatim code duplication detected with Alex Chen"}]),
            # 4: David Kim - Oct 28, 18:45 (On time, verbatim identical to Alex Chen)
            (alex_code.replace("Alex Chen", "David Kim"), datetime(2026, 10, 28, 18, 45), 0.96, [{"with_student": "Alex Chen", "student_id": student_users[0].id, "score": 0.96, "percentage": "96%", "reason": "Verbatim code duplication detected with Alex Chen"}]),
            # 5: Sophia Taylor - Oct 28, 20:10 (On time)
            (f"# ReAct Cognitive Engine by Sophia Taylor\nclass SophiaReAct:\n    def __init__(self):\n        self.steps = []\n    def run(self): return 'ok'", datetime(2026, 10, 28, 20, 10), 0.14, None),
            # 6: Liam Wilson - Oct 28, 22:50 (On time, 1 hour before deadline)
            (f"# ReAct Cognitive Engine by Liam Wilson\nclass LiamReAct:\n    def __init__(self):\n        self.steps = []\n    def execute(self): return True", datetime(2026, 10, 28, 22, 50), 0.16, None),
            # 7: Emma Davis - Oct 29, 08:30 (Late by 8.5 hours past Oct 28 23:59 deadline)
            (f"# ReAct agent by Emma Davis\nclass EmmaAgent:\n    def __init__(self):\n        self.tools = []\n    def act(self): return 'done'", datetime(2026, 10, 29, 8, 30), 0.11, None),
            # 8: Noah Martinez - Oct 30, 11:20 (Late by 1.5 days past deadline)
            (f"# ReAct agent by Noah Martinez\nclass NoahAgent:\n    def step(self): return 'ok'", datetime(2026, 10, 30, 11, 20), 0.18, None),
            # 9: Olivia Brown - Oct 31, 15:00 (Late by 2.6 days past deadline)
            (f"# ReAct implementation Olivia Brown\ndef solve(): return 'done'", datetime(2026, 10, 31, 15, 0), 0.08, None),
            # 10: Lucas Garcia - Oct 26, 09:00 (On time)
            (f"# ReAct tool agent Lucas Garcia\nclass LucasAgent:\n    def run(self): return True", datetime(2026, 10, 26, 9, 0), 0.12, None),
            # 11: Mia Rodriguez - Oct 27, 13:40 (On time)
            (f"# ReAct loop by Mia Rodriguez\nclass MiaAgent:\n    def step(self): return True", datetime(2026, 10, 27, 13, 40), 0.15, None),
        ]

        submission_records = []
        for idx, student in enumerate(student_users[:12]):
            s_name_slug = student.name.lower().replace(" ", "_")
            code_body, sub_time, sim_score, sim_flags_obj = student_sub_specs[idx]
            is_late = (sub_time > asgn1.due_date)

            fn = f"sub_{asgn1.id}_{s_name_slug}.py"
            fp = sub_dir / fn
            fp.write_text(code_body)

            sub = Submission(
                assignment_id=asgn1.id,
                student_id=student.id,
                file_path=str(fp),
                file_name=fn,
                submitted_at=sub_time,
                is_late=is_late,
                similarity_score=sim_score,
                similarity_flags=json.dumps(sim_flags_obj) if sim_flags_obj else None,
                status="submitted"
            )
            session.add(sub)
            submission_records.append((sub, student, is_late, (sim_score > 0.75), idx))

        await session.flush()

        # Seed Grades for submissions
        grade_records = []
        for sub, student, is_late, is_plag, idx in submission_records:
            if is_plag:
                # Plagiarism case: held for human faculty review
                g = Grade(
                    submission_id=sub.id,
                    draft_marks=0.0,
                    draft_feedback="CRITICAL FLAGGED: 96% verbatim similarity detected against Alex Chen's submission. Zero marks drafted. Held for manual faculty review.",
                    draft_rubric_breakdown=json.dumps({
                        "code_correctness": {"marks": 0, "max": 40, "comment": "Unoriginal code matching Alex Chen"},
                        "react_loop_reasoning": {"marks": 0, "max": 25, "comment": "Unoriginal trace"},
                        "error_handling": {"marks": 0, "max": 20, "comment": "Unoriginal"},
                        "documentation": {"marks": 0, "max": 15, "comment": "Unoriginal"}
                    }),
                    evidence_record=json.dumps({"similarity_score": 0.96, "severity": "CRITICAL", "matched_with": "Alex Chen"}),
                    final_marks=None,
                    final_feedback=None,
                    status=GradeStatus.pending_approval,
                    created_at=datetime.utcnow()
                )
            elif is_late:
                # Late submission: 10% deduction
                raw_score = 85.0
                penalized = round(raw_score * 0.90, 1)
                g = Grade(
                    submission_id=sub.id,
                    draft_marks=penalized,
                    draft_feedback=f"Solid implementation. Late submission penalty applied (-10% deduction): {raw_score} -> {penalized} (Submitted past Oct 28 deadline).",
                    draft_rubric_breakdown=json.dumps({
                        "code_correctness": {"marks": 35, "max": 40, "comment": "Working tool loop"},
                        "react_loop_reasoning": {"marks": 22, "max": 25, "comment": "Clear reasoning traces"},
                        "error_handling": {"marks": 15, "max": 20, "comment": "Basic retry logic"},
                        "documentation": {"marks": 13, "max": 15, "comment": "Adequate docstrings"},
                        "late_penalty": {"marks": -8.5, "max": 0, "comment": "-10% deduction for late submission"}
                    }),
                    evidence_record=json.dumps({"on_time": False, "penalty_percent": 10.0, "due_date": asgn1.due_date.isoformat()}),
                    final_marks=None,
                    final_feedback=None,
                    status=GradeStatus.pending_approval,
                    created_at=datetime.utcnow()
                )
            else:
                score = round(88.0 + (idx % 6) * 1.5, 1)
                is_published = (idx in (0, 1))  # Alex Chen and Priya Sharma published
                g = Grade(
                    submission_id=sub.id,
                    draft_marks=score,
                    draft_feedback=f"Excellent work. Clean ReAct loop with proper tool separation. Scored {score}/100.",
                    draft_rubric_breakdown=json.dumps({
                        "code_correctness": {"marks": 36, "max": 40, "comment": "Deterministic tool execution; correct loop"},
                        "react_loop_reasoning": {"marks": 23, "max": 25, "comment": "Thought-Action-Observation sequence cleanly structured"},
                        "error_handling": {"marks": 18, "max": 20, "comment": "Handled tool failure with fallback retries"},
                        "documentation": {"marks": round(score - 77, 1), "max": 15, "comment": "Clear architecture spec and PEP-8 docstrings"}
                    }),
                    evidence_record=json.dumps({"citations": 4, "grounding_coverage": "94%", "on_time": True}),
                    final_marks=score if is_published else None,
                    final_feedback=f"Approved by Faculty: {score}/100" if is_published else None,
                    status=GradeStatus.published if is_published else GradeStatus.pending_approval,
                    approved_by=courses[0].faculty_id if is_published else None,
                    approved_at=datetime.utcnow() - timedelta(hours=12) if is_published else None,
                    published_at=datetime.utcnow() - timedelta(hours=10) if is_published else None
                )
            session.add(g)
            grade_records.append(g)

        await session.flush()
        print(f"  -> Generated {len(submission_records)} Submissions and {len(grade_records)} Evaluated Grades.")

        # 7. Seed Project Groups with Linked GitHub Repositories & Checkpoints
        print("\n[7/7] Seeding Project Groups with GitHub Repositories & Milestone Checkpoints...")
        project_groups = [
            # CS401 Groups (Agentic AI — Dr. Uday Kulkarni)
            ProjectGroup(
                course_id=courses[0].id,
                name="Team Alpha: Autonomous Literature Synthesis Agent",
                description="Scientific paper synthesis and evidence validation multi-agent swarm using LangGraph.",
                github_url="https://github.com/alexchen/agentic-ai-literature-synthesis"
            ),
            ProjectGroup(
                course_id=courses[0].id,
                name="Team Beta: Automated Lab Grading Bot",
                description="Multi-agent swarm for auto-grading AST/PEP-8 Python submissions with human faculty gate.",
                github_url="https://github.com/priyasharma/automated-lab-grading-bot"
            ),
            ProjectGroup(
                course_id=courses[0].id,
                name="Team Gamma: Agentic Course Scheduler",
                description="StateGraph optimizer for exam schedules, classrooms, and proctor assignments.",
                github_url="https://github.com/marcusvance/agentic-course-scheduler"
            ),
            ProjectGroup(
                course_id=courses[0].id,
                name="Team Delta: Safe Code Review Bot",
                description="Security governance bot checking prompt injections and credential leaks.",
                github_url="https://github.com/elenarostova/safe-code-review-bot"
            ),

            # CS402 Groups (Generative AI — Dr. Uday Kulkarni)
            ProjectGroup(
                course_id=courses[1].id,
                name="Team Diffusion: Latent Conditioning Pipeline",
                description="Conditional diffusion architecture for technical schematic and diagram generation.",
                github_url="https://github.com/emilyzhang/latent-diffusion-schematics"
            ),
            ProjectGroup(
                course_id=courses[1].id,
                name="Team Enterprise-RAG: Hybrid Search Engine",
                description="Enterprise multimodal retrieval system with hybrid BM25/Dense fusion and cross-encoder.",
                github_url="https://github.com/liamoconnor/enterprise-hybrid-rag"
            ),

            # CS301 Groups (Machine Learning — Dr. Uday Kulkarni)
            ProjectGroup(
                course_id=courses[2].id,
                name="Team FraudML: Real-Time Anomaly Detector",
                description="High-throughput financial transaction fraud detection using XGBoost and autoencoders.",
                github_url="https://github.com/davidkim/realtime-fraud-ml"
            ),
            ProjectGroup(
                course_id=courses[2].id,
                name="Team Ensemble: Clinical Risk Predictor",
                description="Multivariate survival analysis and gradient-boosted risk stratification.",
                github_url="https://github.com/sophiamartinez/clinical-risk-ensemble"
            ),

            # CS302 Groups (Prof. Rajesh Raman)
            ProjectGroup(
                course_id=courses[3].id,
                name="Team Raft: High-Availability Consensus Cluster",
                description="High-availability Raft consensus cluster with network partition chaos testing.",
                github_url="https://github.com/tariq/raft-consensus-cluster"
            ),
            ProjectGroup(
                course_id=courses[3].id,
                name="Team Vector: Distributed Dynamo Key-Value Store",
                description="Dynamo-inspired distributed key-value store with read repair and vector clocks.",
                github_url="https://github.com/chloe/distributed-dynamo-kv"
            ),
        ]
        session.add_all(project_groups)
        await session.flush()

        # Assign members to groups (3-4 per team, each student is in 1 team per course)
        group_members = [
            # CS401 Group 0: Team Alpha (Alex, Priya, Marcus)
            GroupMember(group_id=project_groups[0].id, student_id=student_users[0].id),
            GroupMember(group_id=project_groups[0].id, student_id=student_users[1].id),
            GroupMember(group_id=project_groups[0].id, student_id=student_users[2].id),
            # CS401 Group 1: Team Beta (Elena, David, Emily)
            GroupMember(group_id=project_groups[1].id, student_id=student_users[3].id),
            GroupMember(group_id=project_groups[1].id, student_id=student_users[4].id),
            GroupMember(group_id=project_groups[1].id, student_id=student_users[5].id),
            # CS401 Group 2: Team Gamma (Liam, Sophia, Tariq)
            GroupMember(group_id=project_groups[2].id, student_id=student_users[6].id),
            GroupMember(group_id=project_groups[2].id, student_id=student_users[7].id),
            GroupMember(group_id=project_groups[2].id, student_id=student_users[8].id),
            # CS401 Group 3: Team Delta (Chloe, Vikram, Zoe, Carlos)
            GroupMember(group_id=project_groups[3].id, student_id=student_users[9].id),
            GroupMember(group_id=project_groups[3].id, student_id=student_users[10].id),
            GroupMember(group_id=project_groups[3].id, student_id=student_users[11].id),
            GroupMember(group_id=project_groups[3].id, student_id=student_users[12].id),

            # CS402 Group 4: Team Diffusion (Alex, Priya, Tariq, Ananya)
            GroupMember(group_id=project_groups[4].id, student_id=student_users[0].id),
            GroupMember(group_id=project_groups[4].id, student_id=student_users[1].id),
            GroupMember(group_id=project_groups[4].id, student_id=student_users[8].id),
            GroupMember(group_id=project_groups[4].id, student_id=student_users[13].id),
            # CS402 Group 5: Team Enterprise-RAG (Elena, Emily, Liam, Kevin)
            GroupMember(group_id=project_groups[5].id, student_id=student_users[3].id),
            GroupMember(group_id=project_groups[5].id, student_id=student_users[5].id),
            GroupMember(group_id=project_groups[5].id, student_id=student_users[6].id),
            GroupMember(group_id=project_groups[5].id, student_id=student_users[14].id),

            # CS301 Group 6: Team FraudML (Marcus, David, Carlos, Sarah)
            GroupMember(group_id=project_groups[6].id, student_id=student_users[2].id),
            GroupMember(group_id=project_groups[6].id, student_id=student_users[4].id),
            GroupMember(group_id=project_groups[6].id, student_id=student_users[12].id),
            GroupMember(group_id=project_groups[6].id, student_id=student_users[15].id),
            # CS301 Group 7: Team Ensemble (Sophia, Chloe, Ethan, Mei)
            GroupMember(group_id=project_groups[7].id, student_id=student_users[7].id),
            GroupMember(group_id=project_groups[7].id, student_id=student_users[9].id),
            GroupMember(group_id=project_groups[7].id, student_id=student_users[16].id),
            GroupMember(group_id=project_groups[7].id, student_id=student_users[17].id),

            # CS302 Group 8: Team Raft (Vikram, Zoe, Ananya)
            GroupMember(group_id=project_groups[8].id, student_id=student_users[10].id),
            GroupMember(group_id=project_groups[8].id, student_id=student_users[11].id),
            GroupMember(group_id=project_groups[8].id, student_id=student_users[13].id),
            # CS302 Group 9: Team Vector (Kevin, Sarah, Ethan)
            GroupMember(group_id=project_groups[9].id, student_id=student_users[14].id),
            GroupMember(group_id=project_groups[9].id, student_id=student_users[15].id),
            GroupMember(group_id=project_groups[9].id, student_id=student_users[16].id),
        ]
        session.add_all(group_members)
        await session.flush()

        # Seed Milestone Checkpoints across courses
        milestones = [
            # CS401 Checkpoints (Agentic AI)
            Milestone(course_id=courses[0].id, title="Checkpoint 1: Problem Spec & Architectural Blueprint", checkpoint_number=1, due_date=datetime.utcnow() - timedelta(days=10)),
            Milestone(course_id=courses[0].id, title="Checkpoint 2: Mid-Term Prototype & MCP Connector", checkpoint_number=2, due_date=datetime.utcnow() + timedelta(days=12)),
            Milestone(course_id=courses[0].id, title="Checkpoint 3: Final Deployment, Safety Rollback & Defense", checkpoint_number=3, due_date=datetime.utcnow() + timedelta(days=35)),

            # CS402 Checkpoints (Generative AI)
            Milestone(course_id=courses[1].id, title="Checkpoint 1: Dataset Curation & LoRA Adapter Topology", checkpoint_number=1, due_date=datetime.utcnow() - timedelta(days=8)),
            Milestone(course_id=courses[1].id, title="Checkpoint 2: Alignment Training & RAG Evaluation", checkpoint_number=2, due_date=datetime.utcnow() + timedelta(days=15)),

            # CS301 Checkpoints (Machine Learning)
            Milestone(course_id=courses[2].id, title="Checkpoint 1: Exploratory Data Analysis & Feature Pipeline", checkpoint_number=1, due_date=datetime.utcnow() - timedelta(days=6)),
            Milestone(course_id=courses[2].id, title="Checkpoint 2: Ensemble Modeling, Cross-Validation & SHAP Analysis", checkpoint_number=2, due_date=datetime.utcnow() + timedelta(days=18)),

            # CS302 Checkpoints (Distributed Systems)
            Milestone(course_id=courses[3].id, title="Checkpoint 1: RPC Protocol & Cluster Topology", checkpoint_number=1, due_date=datetime.utcnow() - timedelta(days=7)),
            Milestone(course_id=courses[3].id, title="Checkpoint 2: Partition Tolerance & Chaos Testing", checkpoint_number=2, due_date=datetime.utcnow() + timedelta(days=20)),
        ]
        session.add_all(milestones)
        await session.flush()

        # Seed Milestone Progress with GitHub links and health status
        progress_entries = [
            # CS401 Teams Progress
            MilestoneProgress(
                milestone_id=milestones[0].id,
                group_id=project_groups[0].id,
                status=MilestoneProgressStatus.approved,
                health=MilestoneHealth.green,
                notes="Completed detailed architecture spec and initial LangGraph node topology. Repository pushed to GitHub.",
                github_url="https://github.com/alexchen/agentic-ai-literature-synthesis",
                submitted_at=datetime.utcnow() - timedelta(days=11)
            ),
            MilestoneProgress(
                milestone_id=milestones[0].id,
                group_id=project_groups[1].id,
                status=MilestoneProgressStatus.submitted,
                health=MilestoneHealth.green,
                notes="Automated grading state machine draft submitted. Ready for faculty review.",
                github_url="https://github.com/priyasharma/automated-lab-grading-bot",
                submitted_at=datetime.utcnow() - timedelta(days=10)
            ),
            MilestoneProgress(
                milestone_id=milestones[0].id,
                group_id=project_groups[2].id,
                status=MilestoneProgressStatus.submitted,
                health=MilestoneHealth.amber,
                notes="Constraint satisfaction algorithm drafted. Facing minor scheduling conflicts.",
                github_url="https://github.com/marcusvance/agentic-course-scheduler",
                submitted_at=datetime.utcnow() - timedelta(days=8)
            ),
            MilestoneProgress(
                milestone_id=milestones[0].id,
                group_id=project_groups[3].id,
                status=MilestoneProgressStatus.not_started,
                health=MilestoneHealth.red,
                notes="Pending initial commit. Team sync scheduled with Dr. Uday Kulkarni.",
                github_url="https://github.com/elenarostova/safe-code-review-bot",
                submitted_at=None
            ),

            # CS402 Teams Progress (Generative AI)
            MilestoneProgress(
                milestone_id=milestones[3].id,
                group_id=project_groups[4].id,
                status=MilestoneProgressStatus.approved,
                health=MilestoneHealth.green,
                notes="VAE latent projection and LoRA adapter weights verified. Complete codebase committed on main.",
                github_url="https://github.com/emilyzhang/latent-diffusion-schematics",
                submitted_at=datetime.utcnow() - timedelta(days=9)
            ),
            MilestoneProgress(
                milestone_id=milestones[3].id,
                group_id=project_groups[5].id,
                status=MilestoneProgressStatus.submitted,
                health=MilestoneHealth.green,
                notes="Milvus vector DB connected. Hybrid search with cross-encoder reranker passing 94% recall.",
                github_url="https://github.com/liamoconnor/enterprise-hybrid-rag",
                submitted_at=datetime.utcnow() - timedelta(days=8)
            ),

            # CS301 Teams Progress (Machine Learning)
            MilestoneProgress(
                milestone_id=milestones[5].id,
                group_id=project_groups[6].id,
                status=MilestoneProgressStatus.approved,
                health=MilestoneHealth.green,
                notes="Kaggle IEEE-CIS fraud dataset preprocessed. Feature importance curves verified.",
                github_url="https://github.com/davidkim/realtime-fraud-ml",
                submitted_at=datetime.utcnow() - timedelta(days=7)
            ),
            MilestoneProgress(
                milestone_id=milestones[5].id,
                group_id=project_groups[7].id,
                status=MilestoneProgressStatus.submitted,
                health=MilestoneHealth.green,
                notes="Random Forest and XGBoost baseline pipelines implemented with 5-fold cross-validation.",
                github_url="https://github.com/sophiamartinez/clinical-risk-ensemble",
                submitted_at=datetime.utcnow() - timedelta(days=6)
            ),
        ]
        session.add_all(progress_entries)
        await session.flush()

        await session.commit()

        print("\n" + "=" * 75)
        print("DATABASE SUCCESSFULLY POPULATED WITH CLASSROOM REAL-WORLD DATASET!")
        print("=" * 75)
        print(f"Faculty Lead:     Dr. Uday Kulkarni (uday.kulkarni@classroom.edu / faculty@classroom.edu)")
        print(f"Courses Total:    {len(courses)} (Agentic AI, Generative AI, Machine Learning, etc.)")
        print(f"Faculty Total:    {len(faculty_users)} (HoD removed)")
        print(f"Students Total:   {len(student_users)}")
        print(f"Notes Total:      {total_notes_created}")
        print(f"Assignments:      {len(created_assignments)}")
        print(f"Submissions:      {len(submission_records)}")
        print(f"Grades:           {len(grade_records)}")
        print(f"Project Groups:   {len(project_groups)} (All with GitHub Repositories)")
        print(f"Password:         'aura@1010' for ALL accounts")
        print("=" * 75)


if __name__ == "__main__":
    asyncio.run(seed_rich_data())
