#!/usr/bin/env python3
"""
Extended Quantum Gate Test Suite
Tests new and advanced quantum gates:
- 1-qubit: p/phase, u1, u2, u3/u, sx, sxdg
- 2-qubit: cy, ch, cp, crx, cry, crz
- 3-qubit: ccx (Toffoli), cswap (Fredkin)
- Complex decompositions (Toffoli Clifford+T decomposition, Fredkin CNOT+Toffoli decomposition)
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "extended_gates_dataset"
QASM_HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'

ALLOWED_OPS = [
    "h", "x", "y", "z", "i", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "cx", "cz", "swap",
    "p", "phase", "u1", "u2", "u3", "u", "sx", "sxdg",
    "cy", "ch", "cp", "crx", "cry", "crz",
    "ccx", "cswap"
]


def make_instance(
    instance_id: str,
    qubit_count: int,
    semantic_mode: str,
    circuit_a_body: str,
    circuit_b_body: str,
    expected_decision: str,
    description: str = "",
) -> dict[str, str]:
    inst_dir = DATASET_DIR / "instances" / instance_id
    inst_dir.mkdir(parents=True, exist_ok=True)

    instance_json = {
        "allowed_operations": ALLOWED_OPS,
        "circuit_a": "circuit_a.qasm",
        "circuit_b": "circuit_b.qasm",
        "instance_id": instance_id,
        "parameter_schema": {},
        "qubit_count": qubit_count,
        "resource_limits": {"tier": "extended_gate_test"},
        "semantic_mode": semantic_mode,
        "description": description,
    }
    (inst_dir / "instance.json").write_text(
        json.dumps(instance_json, indent=2) + "\n", encoding="utf-8"
    )

    qasm_a = QASM_HEADER + f"qubit[{qubit_count}] q;\n" + circuit_a_body
    (inst_dir / "circuit_a.qasm").write_text(qasm_a, encoding="utf-8")

    qasm_b = QASM_HEADER + f"qubit[{qubit_count}] q;\n" + circuit_b_body
    (inst_dir / "circuit_b.qasm").write_text(qasm_b, encoding="utf-8")

    return {
        "instance_id": instance_id,
        "decision": expected_decision,
        "mode": semantic_mode,
        "description": description,
    }


def build_extended_dataset() -> list[dict[str, str]]:
    tests = []

    # =========================================================================
    # 1. Square-Root of X (sx and sxdg)
    # =========================================================================
    # sx · sx == x
    tests.append(make_instance(
        "ext_sx_square_is_x",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="sx q[0];\nsx q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="EQUIVALENT",
        description="sx · sx = x (two sqrt-X gates produce X)",
    ))

    # sx · sxdg == I
    tests.append(make_instance(
        "ext_sx_sxdg_cancel",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="sx q[0];\nsxdg q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
        description="sx · sxdg = I (sqrt-X and its adjoint cancel)",
    ))

    # sx != x
    tests.append(make_instance(
        "ext_sx_vs_x_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="sx q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="sx != x (sqrt-X is not X)",
    ))

    # =========================================================================
    # 2. Phase Gates (p, phase, u1)
    # =========================================================================
    # p(pi) == z
    tests.append(make_instance(
        "ext_p_pi_is_z",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="p(pi) q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="EQUIVALENT",
        description="p(pi) = z (phase gate at pi is Z)",
    ))

    # p(pi/2) == s
    tests.append(make_instance(
        "ext_p_half_pi_is_s",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="p(pi/2) q[0];\n",
        circuit_b_body="s q[0];\n",
        expected_decision="EQUIVALENT",
        description="p(pi/2) = s (phase gate at pi/2 is S)",
    ))

    # p(pi/4) == t
    tests.append(make_instance(
        "ext_p_quarter_pi_is_t",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="p(pi/4) q[0];\n",
        circuit_b_body="t q[0];\n",
        expected_decision="EQUIVALENT",
        description="p(pi/4) = t (phase gate at pi/4 is T)",
    ))

    # u1(pi) == z
    tests.append(make_instance(
        "ext_u1_is_p",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="u1(pi) q[0];\n",
        circuit_b_body="p(pi) q[0];\n",
        expected_decision="EQUIVALENT",
        description="u1(lambda) = p(lambda)",
    ))

    # p(pi/3) != p(pi/4)
    tests.append(make_instance(
        "ext_p_diff_angles_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="p(pi/3) q[0];\n",
        circuit_b_body="p(pi/4) q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="p(pi/3) != p(pi/4)",
    ))

    # =========================================================================
    # 3. Arbitrary Single Qubit Unitary Gates (u2, u3, u)
    # =========================================================================
    # u3(pi/2, 0, pi) == h
    tests.append(make_instance(
        "ext_u3_hadamard",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="u3(pi/2, 0, pi) q[0];\n",
        circuit_b_body="h q[0];\n",
        expected_decision="EQUIVALENT",
        description="u3(pi/2, 0, pi) = H (Hadamard via U3)",
    ))

    # u3(pi, 0, pi) == x
    tests.append(make_instance(
        "ext_u3_pauli_x",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="u3(pi, 0, pi) q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="EQUIVALENT",
        description="u3(pi, 0, pi) = X (Pauli-X via U3)",
    ))

    # u2(0, pi) == h
    tests.append(make_instance(
        "ext_u2_hadamard",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="u2(0, pi) q[0];\n",
        circuit_b_body="h q[0];\n",
        expected_decision="EQUIVALENT",
        description="u2(0, pi) = H (Hadamard via U2)",
    ))

    # u(pi/4, pi/3, pi/6) vs different parameters -> NON_EQUIVALENT
    tests.append(make_instance(
        "ext_u3_mismatched_params",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="u3(pi/4, pi/3, pi/6) q[0];\n",
        circuit_b_body="u3(pi/4, pi/3, pi/5) q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="u3 with different lambda parameters is non-equivalent",
    ))

    # =========================================================================
    # 4. Controlled 1-Qubit Gates (cy, ch, cp)
    # =========================================================================
    # cy · cy == I
    tests.append(make_instance(
        "ext_cy_involution",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cy q[0], q[1];\ncy q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
        description="cy · cy = I (Controlled-Y is self-inverse)",
    ))

    # ch · ch == I
    tests.append(make_instance(
        "ext_ch_involution",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="ch q[0], q[1];\nch q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
        description="ch · ch = I (Controlled-H is self-inverse)",
    ))

    # S(1) · cx(0,1) · Sdg(1) == cy(0,1)
    tests.append(make_instance(
        "ext_cy_from_cx_s",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="sdg q[1];\ncx q[0], q[1];\ns q[1];\n",
        circuit_b_body="cy q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="sdg(1) cx(0,1) s(1) = cy(0,1) exact equivalence",
    ))

    # cp(pi) == cz
    tests.append(make_instance(
        "ext_cp_pi_is_cz",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cp(pi) q[0], q[1];\n",
        circuit_b_body="cz q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="cp(pi) = cz (Controlled Phase at pi is CZ)",
    ))

    # ch != cx
    tests.append(make_instance(
        "ext_ch_vs_cx_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="ch q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="ch != cx (Controlled-H is not CNOT)",
    ))

    # =========================================================================
    # 5. Controlled Rotations (crx, cry, crz)
    # =========================================================================
    # crz(2*pi) == I (rotation of 2pi is identity up to global phase / exact phase check)
    # Note: Rz(2*pi) has e^(-i*pi) = -1 on diagonal, so crz(2*pi) has -1 on |11>.
    # Instead test crz(4*pi) == I:
    tests.append(make_instance(
        "ext_crz_4pi_identity",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="crz(4*pi) q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
        description="crz(4*pi) = I",
    ))

    # crx(pi/2) · crx(-pi/2) == I
    tests.append(make_instance(
        "ext_crx_cancel",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="crx(pi/2) q[0], q[1];\ncrx(-pi/2) q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
        description="crx(theta) · crx(-theta) = I",
    ))

    # =========================================================================
    # 6. 3-Qubit Gates: Toffoli (ccx) and Fredkin (cswap)
    # =========================================================================
    # ccx · ccx == I
    tests.append(make_instance(
        "ext_ccx_involution",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="ccx q[0], q[1], q[2];\nccx q[0], q[1], q[2];\n",
        circuit_b_body="i q[0];\ni q[1];\ni q[2];\n",
        expected_decision="EQUIVALENT",
        description="ccx · ccx = I (Toffoli gate is self-inverse)",
    ))

    # cswap · cswap == I
    tests.append(make_instance(
        "ext_cswap_involution",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="cswap q[0], q[1], q[2];\ncswap q[0], q[1], q[2];\n",
        circuit_b_body="i q[0];\ni q[1];\ni q[2];\n",
        expected_decision="EQUIVALENT",
        description="cswap · cswap = I (Fredkin gate is self-inverse)",
    ))

    # Canonical Clifford+T decomposition of Toffoli (15 gates) vs direct ccx
    toffoli_decomp = (
        "h q[2];\n"
        "cx q[1], q[2];\n"
        "tdg q[2];\n"
        "cx q[0], q[2];\n"
        "t q[2];\n"
        "cx q[1], q[2];\n"
        "tdg q[2];\n"
        "cx q[0], q[2];\n"
        "t q[1];\n"
        "t q[2];\n"
        "h q[2];\n"
        "cx q[0], q[1];\n"
        "t q[0];\n"
        "tdg q[1];\n"
        "cx q[0], q[1];\n"
    )
    tests.append(make_instance(
        "ext_toffoli_clifford_t_equiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body=toffoli_decomp,
        circuit_b_body="ccx q[0], q[1], q[2];\n",
        expected_decision="EQUIVALENT",
        description="Canonical 15-gate Clifford+T decomposition of Toffoli == direct ccx",
    ))

    # Corrupted Toffoli decomposition (replace last tdg with t) -> NON_EQUIVALENT
    corrupted_toffoli = (
        "h q[2];\n"
        "cx q[1], q[2];\n"
        "tdg q[2];\n"
        "cx q[0], q[2];\n"
        "t q[2];\n"
        "cx q[1], q[2];\n"
        "tdg q[2];\n"
        "cx q[0], q[2];\n"
        "t q[1];\n"
        "t q[2];\n"
        "h q[2];\n"
        "cx q[0], q[1];\n"
        "t q[0];\n"
        "t q[1];\n"  # Corrupted: t instead of tdg
        "cx q[0], q[1];\n"
    )
    tests.append(make_instance(
        "ext_toffoli_corrupted_nonequiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body=corrupted_toffoli,
        circuit_b_body="ccx q[0], q[1], q[2];\n",
        expected_decision="NON_EQUIVALENT",
        description="Corrupted Toffoli decomposition != direct ccx",
    ))

    # Fredkin decomposition using 2 CNOTs and 1 Toffoli:
    # cx q[2], q[1]; ccx q[0], q[1], q[2]; cx q[2], q[1]; == cswap q[0], q[1], q[2]
    tests.append(make_instance(
        "ext_fredkin_cnot_toffoli_equiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[2], q[1];\nccx q[0], q[1], q[2];\ncx q[2], q[1];\n",
        circuit_b_body="cswap q[0], q[1], q[2];\n",
        expected_decision="EQUIVALENT",
        description="Fredkin (CSWAP) decomposed into CNOT + Toffoli + CNOT",
    ))

    # =========================================================================
    # 7. Global Phase vs Exact Unitary with Extended Gates
    # =========================================================================
    # Rz(pi) vs Z:
    # Rz(pi) = [[-i, 0], [0, i]] = -i * [[1, 0], [0, -1]] = -i * Z
    # In exact mode -> NON_EQUIVALENT
    # In global phase mode -> EQUIVALENT
    tests.append(make_instance(
        "ext_rz_pi_vs_z_exact",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="rz(pi) q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="rz(pi) has -i global phase relative to z (exact mode: NON_EQUIVALENT)",
    ))

    tests.append(make_instance(
        "ext_rz_pi_vs_z_phase",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body="rz(pi) q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="EQUIVALENT",
        description="rz(pi) has -i global phase relative to z (phase mode: EQUIVALENT)",
    ))

    # Write manifest and answer key
    inst_ids = [t["instance_id"] for t in tests]
    manifest = {
        "dataset_id": "extended_gates_v1",
        "public_answer_key": "answers.json",
        "instances": inst_ids
    }
    (DATASET_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    answer_list = [{"instance_id": t["instance_id"], "decision": t["decision"]} for t in tests]
    (DATASET_DIR / "answers.json").write_text(
        json.dumps({"answers": answer_list}, indent=2) + "\n", encoding="utf-8"
    )

    return tests


def run_tests():
    print("=" * 75)
    print("Generating Extended Quantum Gate Test Suite...")
    print("=" * 75)
    tests = build_extended_dataset()
    print(f"Generated {len(tests)} test instances in {DATASET_DIR}\n")

    python_exe = sys.executable
    solver_script = ROOT / "submission" / "run.py"

    passed = 0
    failed = 0
    results_detail = []

    print(f"{'#':<3} {'Instance ID':<32} {'Mode':<15} {'Expected':<14} {'Actual':<14} {'Result'}")
    print("-" * 88)

    total_start = time.perf_counter()

    for idx, t in enumerate(tests, 1):
        inst_id = t["instance_id"]
        inst_dir = DATASET_DIR / "instances" / inst_id
        expected = t["decision"]

        t0 = time.perf_counter()
        proc = subprocess.run(
            [python_exe, str(solver_script), str(inst_dir)],
            capture_output=True,
            text=True,
        )
        elapsed = (time.perf_counter() - t0) * 1000

        actual = "CRASH"
        method_used = "N/A"
        if proc.returncode == 0:
            try:
                out_data = json.loads(proc.stdout.strip())
                actual = out_data.get("decision", "INVALID_JSON")
                method_used = out_data.get("evidence", {}).get("method", "N/A")
            except Exception:
                actual = "BAD_JSON"

        is_correct = (actual == expected)
        status_sym = "[OK] PASS" if is_correct else "[X] FAIL"

        if is_correct:
            passed += 1
        else:
            failed += 1

        results_detail.append({
            "id": inst_id,
            "mode": t["mode"],
            "expected": expected,
            "actual": actual,
            "passed": is_correct,
            "elapsed_ms": round(elapsed, 2),
            "description": t["description"],
            "method": method_used,
        })

        print(f"{idx:<3} {inst_id:<32} {t['mode']:<15} {expected:<14} {actual:<14} {status_sym}")

    total_elapsed = time.perf_counter() - total_start

    print("-" * 88)
    print(f"RESULTS: {passed}/{len(tests)} Passed (Accuracy: {passed / len(tests) * 100:.1f}%) in {total_elapsed:.2f}s")
    print("=" * 75)

    # Save detailed report
    report_file = ROOT / "extended_gates_test_report.json"
    report_data = {
        "total": len(tests),
        "passed": passed,
        "failed": failed,
        "accuracy": passed / len(tests),
        "elapsed_seconds": round(total_elapsed, 3),
        "tests": results_detail,
    }
    report_file.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    print(f"Detailed report saved to {report_file}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
