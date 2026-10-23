#!/usr/bin/env python3
"""
Structural Similar Pairs Test Suite
Modeled directly on public benchmark instance 'dev_structural_001'.
Tests pairs of quantum circuits with nearly identical physical structure:
- Paired contrasts: one version is EQUIVALENT (valid identity/commutation),
  and its structurally almost-identical twin is NON_EQUIVALENT (adversarial bug/near-miss).
- Categories:
  1. Identity insertion / cancellation (X·X, Z·Z, H·H, S·Sdg vs S·S bug)
  2. Commutation relations (commuting on different wires vs non-commuting reordering)
  3. CNOT control/target propagation rules (Z commutes with control, X commutes with target)
  4. Control-target symmetry: CZ is symmetric (CZ_01 == CZ_10), CX is NOT (CX_01 != CX_10)
  5. Parametric rotation cancellation vs sign/angle error
  6. Global phase insertion in exact vs global phase mode
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "structural_pairs_dataset"
QASM_HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'

ALLOWED_OPS = [
    "h", "x", "y", "z", "i", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "cx", "cz", "swap"
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
        "resource_limits": {"tier": "structural_pair_test"},
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


def build_structural_dataset() -> list[dict[str, str]]:
    tests = []

    # =========================================================================
    # Pair Group 1: Middle-Circuit Identity Insertion (X-X, Z-Z)
    # =========================================================================
    # 1A. Equivalent: Z-Z cancellation inserted into Bell circuit
    tests.append(make_instance(
        "struct_pair_01_zz_cancel_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\nz q[1];\nz q[1];\nh q[0];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\nh q[0];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Circuit A has redundant z q[1]; z q[1]; (Z·Z = I)",
    ))

    # 1B. Non-Equivalent: Single Z inserted (omitted second Z)
    tests.append(make_instance(
        "struct_pair_02_single_z_bug_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\nz q[1];\nh q[0];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\nh q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: Circuit A has single z q[1] instead of pair",
    ))

    # =========================================================================
    # Pair Group 2: S vs S-Dagger (Adjoint Omission Bug)
    # =========================================================================
    # 2A. Equivalent: S followed by Sdg cancels
    tests.append(make_instance(
        "struct_pair_03_s_sdg_cancel_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ns q[1];\nsdg q[1];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Circuit A has s q[1]; sdg q[1]; (S·Sdg = I)",
    ))

    # 2B. Non-Equivalent: S followed by S (accidental S instead of Sdg)
    tests.append(make_instance(
        "struct_pair_04_s_s_omitted_dagger_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ns q[1];\ns q[1];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: s q[1]; s q[1] equals Z, not I",
    ))

    # =========================================================================
    # Pair Group 3: Commutation on Disjoint Qubits
    # =========================================================================
    # 3A. Equivalent: Reordering operations on independent qubits
    tests.append(make_instance(
        "struct_pair_05_disjoint_commute_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nx q[1];\ncx q[0], q[1];\nz q[0];\ns q[1];\n",
        circuit_b_body="x q[1];\nh q[0];\ncx q[0], q[1];\ns q[1];\nz q[0];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Independent single-qubit gates reordered",
    ))

    # 3B. Non-Equivalent: Reordering operations on SAME qubit (H and Z do NOT commute)
    tests.append(make_instance(
        "struct_pair_06_same_wire_reorder_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nz q[0];\ncx q[0], q[1];\n",
        circuit_b_body="z q[0];\nh q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: H·Z != Z·H on same qubit",
    ))

    # =========================================================================
    # Pair Group 4: CNOT Control Wire Commutation (Z commutes with Control)
    # =========================================================================
    # 4A. Equivalent: Z commutes past CNOT control qubit
    tests.append(make_instance(
        "struct_pair_07_cnot_control_z_commute_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="z q[0];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\nz q[0];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Z commutes with the control qubit of CNOT",
    ))

    # 4B. Non-Equivalent: Z does NOT commute past CNOT target qubit
    tests.append(make_instance(
        "struct_pair_08_cnot_target_z_noncommute_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="z q[1];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\nz q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: Z does NOT commute with the target qubit of CNOT",
    ))

    # =========================================================================
    # Pair Group 5: CNOT Target Wire Commutation (X commutes with Target)
    # =========================================================================
    # 5A. Equivalent: X commutes past CNOT target qubit
    tests.append(make_instance(
        "struct_pair_09_cnot_target_x_commute_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="x q[1];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\nx q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: X commutes with the target qubit of CNOT",
    ))

    # 5B. Non-Equivalent: X does NOT commute past CNOT control qubit
    tests.append(make_instance(
        "struct_pair_10_cnot_control_x_noncommute_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="x q[0];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\nx q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: X does NOT commute with the control qubit of CNOT",
    ))

    # =========================================================================
    # Pair Group 6: Two-Qubit Gate Symmetry (CZ is Symmetric, CX is NOT)
    # =========================================================================
    # 6A. Equivalent: Controlled-Z is symmetric under control-target swap
    tests.append(make_instance(
        "struct_pair_11_cz_symmetric_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncz q[0], q[1];\nh q[1];\n",
        circuit_b_body="h q[0];\ncz q[1], q[0];\nh q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: cz q[0], q[1] == cz q[1], q[0]",
    ))

    # 6B. Non-Equivalent: Controlled-X (CNOT) is NOT symmetric under control-target swap
    tests.append(make_instance(
        "struct_pair_12_cx_asymmetric_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\nh q[1];\n",
        circuit_b_body="h q[0];\ncx q[1], q[0];\nh q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: cx q[0], q[1] != cx q[1], q[0]",
    ))

    # =========================================================================
    # Pair Group 7: Parametric Rotation Inverse Cancellation vs Sign Bug
    # =========================================================================
    # 7A. Equivalent: Rx(theta) and Rx(-theta) cancel out
    tests.append(make_instance(
        "struct_pair_13_rx_inv_cancel_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nrx(pi/3) q[1];\nrx(-pi/3) q[1];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: rx(pi/3) and rx(-pi/3) cancel to identity",
    ))

    # 7B. Non-Equivalent: Both have positive sign (rx(pi/3) rx(pi/3) = rx(2pi/3) != I)
    tests.append(make_instance(
        "struct_pair_14_rx_sign_error_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nrx(pi/3) q[1];\nrx(pi/3) q[1];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: missing negative sign in rotation angle",
    ))

    # =========================================================================
    # Pair Group 8: Multi-Qubit Qubit Target Indexing (q[1] vs q[2])
    # =========================================================================
    # 8A. Equivalent: Identity wire explicitly padded
    tests.append(make_instance(
        "struct_pair_15_idle_wire_padding_equiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\ni q[2];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Explicit identity gate on idle wire q[2]",
    ))

    # 8B. Non-Equivalent: Target wire index typo (q[2] instead of q[1])
    tests.append(make_instance(
        "struct_pair_16_target_wire_typo_nonequiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[2];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: CNOT connects to wire 2 instead of wire 1",
    ))

    # =========================================================================
    # Pair Group 9: Full 2*pi Rotation: Exact vs Global Phase Mode
    # =========================================================================
    # 9A. Equivalent: Rz(2*pi) is -I, ignored in global_phase_unitary mode
    tests.append(make_instance(
        "struct_pair_17_rz_2pi_phase_equiv",
        qubit_count=2,
        semantic_mode="global_phase_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\nrz(2*pi) q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: Rz(2*pi) adds -1 global phase (EQUIVALENT in phase mode)",
    ))

    # 9B. Non-Equivalent: Under exact_unitary mode, -I is NOT equivalent to I
    tests.append(make_instance(
        "struct_pair_18_rz_2pi_exact_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\nrz(2*pi) q[1];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar: Rz(2*pi) adds -1 global phase (NON_EQUIVALENT in exact mode)",
    ))

    # =========================================================================
    # Pair Group 10: Hadamard Sandwich Cancellation (H·X·H = Z)
    # =========================================================================
    # 10A. Equivalent: H·X·H correctly replaced by Z
    tests.append(make_instance(
        "struct_pair_19_hadamard_conjugation_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nh q[0];\nx q[0];\nh q[0];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\nz q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="Structurally similar: H·X·H == Z identity substitution",
    ))

    # 10B. Non-Equivalent: H·X·H mistakenly replaced by X instead of Z
    tests.append(make_instance(
        "struct_pair_20_hadamard_conjugation_bug_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nh q[0];\nx q[0];\nh q[0];\ncx q[0], q[1];\n",
        circuit_b_body="h q[0];\nx q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Structurally similar bug: H·X·H is Z, not X",
    ))

    # Write manifest and answer key matching evaluator protocol
    inst_ids = [t["instance_id"] for t in tests]
    manifest = {
        "dataset_id": "structural_pairs_v1",
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
    print("=" * 85)
    print("  STRUCTURAL SIMILAR PAIRS TEST SUITE (Modelled on dev_structural_001)")
    print("=" * 85)
    tests = build_structural_dataset()
    print(f"Generated {len(tests)} structurally similar test instances in {DATASET_DIR}\n")

    python_exe = sys.executable
    solver_script = ROOT / "submission" / "run.py"

    passed = 0
    failed = 0
    results_detail = []

    print(f"{'#':<3} {'Instance ID':<50} {'Mode':<15} {'Expected':<14} {'Actual':<14} {'Result'}")
    print("-" * 105)

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

        print(f"{idx:<3} {inst_id:<50} {t['mode']:<15} {expected:<14} {actual:<14} {status_sym}")

    total_elapsed = time.perf_counter() - total_start

    print("-" * 105)
    print(f"RESULTS: {passed}/{len(tests)} Passed (Accuracy: {passed / len(tests) * 100:.1f}%) in {total_elapsed:.2f}s")
    print("=" * 85)

    report_file = ROOT / "structural_pairs_test_report.json"
    report_data = {
        "total": len(tests),
        "passed": passed,
        "failed": failed,
        "accuracy": passed / len(tests),
        "elapsed_seconds": round(total_elapsed, 3),
        "tests": results_detail,
    }
    report_file.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    print(f"Detailed structural pair report saved to {report_file}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
