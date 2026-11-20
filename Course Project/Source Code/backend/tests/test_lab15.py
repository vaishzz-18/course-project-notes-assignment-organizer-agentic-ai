"""
Lab 15: Winning Advantage — Examiner Live Defense & Multi-Agent Stress Benchmark
Test Suite
Chapter 2: Course Project, Notes & Assignment Organizer
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from runtime.defense_benchmark import (
    ExaminerDefenseEngine,
    STANDARD_ATTACK_VECTORS,
    AdversarialAttackVector,
    StressMetrics,
    DefenseCertificate,
)
from api.main import app


@pytest.fixture
def engine():
    return ExaminerDefenseEngine()


@pytest.fixture
def client():
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 15-Lab Compliance Matrix Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestComplianceMatrix:
    def test_compliance_matrix_has_15_labs(self, engine):
        matrix = engine.get_compliance_matrix()
        assert len(matrix) == 15, f"Expected 15 labs, found {len(matrix)}"

    def test_all_15_labs_verified_operational(self, engine):
        matrix = engine.get_compliance_matrix()
        for item in matrix:
            assert item.verification_status == "VERIFIED_OPERATIONAL", (
                f"Lab {item.lab_id} ({item.name}) status is {item.verification_status}"
            )

    def test_phases_coverage(self, engine):
        matrix = engine.get_compliance_matrix()
        phases = {item.phase for item in matrix}
        expected_phases = {
            "Phase A: Foundations",
            "Phase B: Multi-Agent Topology",
            "Phase C: Applied Reliability",
            "Phase D: Governance & Capstone",
        }
        assert phases == expected_phases, f"Missing phases: {expected_phases - phases}"

    def test_key_symbols_present(self, engine):
        matrix = engine.get_compliance_matrix()
        for item in matrix:
            assert len(item.key_symbols) >= 2, f"Lab {item.lab_id} must list key symbols"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Multi-Agent Concurrency Stress Benchmark Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiAgentStressBenchmark:
    def test_stress_benchmark_execution(self, engine):
        metrics = asyncio.run(engine.run_stress_benchmark(concurrency=10, iterations_per_worker=2))
        assert isinstance(metrics, StressMetrics)
        assert metrics.total_requests == 20
        assert metrics.successful_requests == 20
        assert metrics.failed_requests == 0
        assert metrics.error_rate_pct == 0.0
        assert metrics.throughput_rps > 0.0

    def test_stress_benchmark_latency_percentiles(self, engine):
        metrics = asyncio.run(engine.run_stress_benchmark(concurrency=8, iterations_per_worker=2))
        assert metrics.latency_p50_ms <= metrics.latency_p95_ms
        assert metrics.latency_p95_ms <= metrics.latency_p99_ms
        assert metrics.latency_p99_ms > 0.0

    def test_governance_budget_not_exhausted(self, engine):
        metrics = asyncio.run(engine.run_stress_benchmark(concurrency=12, iterations_per_worker=1))
        assert metrics.governance_budget_exhausted is False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Adversarial Defense Harness Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdversarialDefenseHarness:
    def test_prompt_injection_neutralization(self, engine):
        atk = STANDARD_ATTACK_VECTORS[0]
        assert atk.category == "PROMPT_INJECTION"
        df = engine.execute_adversarial_defense(atk)
        assert df.attack_detected is True
        assert df.attack_neutralized is True
        assert df.security_verdict == "DEFENSE_SUCCESSFUL"
        assert len(df.audit_hash) == 64

    def test_grade_tampering_clamp(self, engine):
        atk = STANDARD_ATTACK_VECTORS[1]
        assert atk.category == "GRADE_TAMPERING"
        df = engine.execute_adversarial_defense(atk)
        assert df.attack_detected is True
        assert df.attack_neutralized is True
        assert df.security_verdict == "DEFENSE_SUCCESSFUL"

    def test_out_of_scope_hallucination_rejection(self, engine):
        atk = STANDARD_ATTACK_VECTORS[2]
        assert atk.category == "OUT_OF_SCOPE_HALLUCINATION"
        df = engine.execute_adversarial_defense(atk)
        assert df.attack_detected is True
        assert df.attack_neutralized is True
        assert df.security_verdict == "DEFENSE_SUCCESSFUL"

    def test_unauthorized_publish_blocked(self, engine):
        atk = STANDARD_ATTACK_VECTORS[3]
        assert atk.category == "UNAUTHORIZED_PUBLISH"
        df = engine.execute_adversarial_defense(atk)
        assert df.attack_detected is True
        assert df.attack_neutralized is True
        assert df.security_verdict == "DEFENSE_SUCCESSFUL"

    def test_privilege_escalation_sanitization(self, engine):
        atk = STANDARD_ATTACK_VECTORS[4]
        assert atk.category == "PRIVILEGE_ESCALATION"
        df = engine.execute_adversarial_defense(atk)
        assert df.attack_detected is True
        assert df.attack_neutralized is True
        assert df.security_verdict == "DEFENSE_SUCCESSFUL"

    def test_run_all_adversarial_defenses_100_percent(self, engine):
        defenses = engine.run_all_adversarial_defenses()
        assert len(defenses) == 5
        for d in defenses:
            assert d.security_verdict == "DEFENSE_SUCCESSFUL"
            assert d.attack_detected is True
            assert d.attack_neutralized is True


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Cryptographic Certificate Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCryptographicCertificate:
    def test_certificate_generation(self, engine):
        cert = engine.generate_defense_certificate()
        assert isinstance(cert, DefenseCertificate)
        assert cert.total_labs_verified == 15
        assert cert.compliance_score == "15/15 (100%)"
        assert len(cert.sha256_audit_fingerprint) == 64
        assert cert.course_code == "CS401"
        assert "Zero Autonomous Consequential Actions" in cert.human_in_the_loop_guarantee


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FastAPI Route Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestLab15ApiEndpoints:
    def test_demo_endpoint(self, client):
        response = client.get("/lab15/demo")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        steps = data["steps"]
        assert steps["step1_compliance_matrix"]["total_labs"] == 15
        assert steps["step1_compliance_matrix"]["verified_operational"] == 15
        assert steps["step2_stress_benchmark"]["successful_requests"] > 0
        assert steps["step3_adversarial_defenses"]["all_neutralized"] is True
        assert len(steps["step4_audit_certificate"]["sha256_audit_fingerprint"]) == 64

    def test_readiness_endpoint(self, client):
        response = client.get("/lab15/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["total_labs"] == 15
        assert data["verified_count"] == 15

    def test_stress_test_endpoint(self, client):
        response = client.post("/lab15/stress-test", json={"concurrency": 8, "iterations": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["metrics"]["total_requests"] == 8

    def test_adversarial_defense_endpoint(self, client):
        response = client.post("/lab15/adversarial-defense", json={"attack_index": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["defense_outcome"]["security_verdict"] == "DEFENSE_SUCCESSFUL"

    def test_certificate_endpoint(self, client):
        response = client.get("/lab15/certificate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["certificate"]["compliance_score"] == "15/15 (100%)"
