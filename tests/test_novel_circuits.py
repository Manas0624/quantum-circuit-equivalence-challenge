#!/usr/bin/env python3
"""
Novel Quantum Algorithm & Circuit Equivalence Test Suite
Tests real-world quantum algorithms, multi-qubit entanglement, and composite gates:
- CNOT Direction Reversal Identity (Hadamard conjugation: H H CX H H == CX)
- Symmetrical 3-CNOT SWAP constructions (CX-CX-CX order invariance)
- State-Preparation vs Full-Unitary Trap (Bell & GHZ state prep circuits differ on non-|00> inputs)
- Controlled-Controlled-Z (CCZ) gate via H + CCX + H
- Quantum Half-Adder & bug detection (gate ordering sensitivity)
- 2-Qubit Grover Diffusion Operator (Inversion about the mean)
- Pauli Commutation anti-symmetry (XZ vs ZX under exact vs global phase)
- Multi-qubit Quantum Teleportation sub-circuit
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "novel_circuits_dataset"
QASM_HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'

ALLOWED_OPS = [
    "h", "x", "y", "z", "i", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "cx", "cz", "swap", "ccx", "cswap"
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
        "resource_limits": {"tier": "novel_circuit_test"},
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


def build_novel_dataset() -> list[dict[str, str]]:
    tests = []

    # 1. CNOT Direction Reversal Theorem:
    # A textbook quantum computing theorem: H on both qubits reverses CNOT control and target!
    # H(0) H(1) CX(1,0) H(0) H(1) == CX(0,1)
    tests.append(make_instance(
        "novel_cnot_direction_reversal_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nh q[1];\ncx q[1], q[0];\nh q[0];\nh q[1];\n",
        circuit_b_body="cx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="CNOT Direction Reversal: H(0) H(1) CX(1,0) H(0) H(1) == CX(0,1)",
    ))

    # 2. Dual Symmetrical 3-CNOT SWAP Constructions:
    # CX(0,1) CX(1,0) CX(0,1) == CX(1,0) CX(0,1) CX(1,0) == SWAP(0,1)
    tests.append(make_instance(
        "novel_swap_cnot_symmetry_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[1], q[0];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[1], q[0];\ncx q[0], q[1];\ncx q[1], q[0];\n",
        expected_decision="EQUIVALENT",
        description="SWAP symmetry: CX(0,1) CX(1,0) CX(0,1) == CX(1,0) CX(0,1) CX(1,0)",
    ))

    # 3. State-Preparation Trap (Bell State):
    # Both circuits prepare (|00> + |11>)/sqrt(2) from |00>, but as unitary operators they differ on |01>!
    # A naive human thinks they are equivalent; the solver correctly proves they are NON_EQUIVALENT!
    tests.append(make_instance(
        "novel_bell_state_unitary_mismatch_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\n",
        circuit_b_body="h q[1];\ncx q[1], q[0];\nswap q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="State-prep trap: Bell generators identical on |00> but differ on |01> (correctly NON_EQUIVALENT)",
    ))

    # 4. State-Preparation Trap (3-Qubit GHZ):
    # Cascaded vs fan-out CNOT both prepare (|000> + |111>)/sqrt(2) from |000>,
    # but produce different unitary transformations on other basis states!
    tests.append(make_instance(
        "novel_ghz_unitary_mismatch_nonequiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\ncx q[0], q[1];\ncx q[1], q[2];\n",
        circuit_b_body="h q[0];\ncx q[0], q[2];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="State-prep trap: 3-qubit GHZ prep circuits differ on general inputs (correctly NON_EQUIVALENT)",
    ))

    # 5. CCZ Gate Construction (Controlled-Controlled-Z):
    # A Controlled-Controlled-Z gate is synthesized by surrounding the target of a Toffoli gate with Hadamards:
    # Control symmetry: CCX(0,1,2) == CCX(1,0,2)
    tests.append(make_instance(
        "novel_ccz_h_toffoli_h_equiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[2];\nccx q[0], q[1], q[2];\nh q[2];\n",
        circuit_b_body="h q[2];\nccx q[1], q[0], q[2];\nh q[2];\n",
        expected_decision="EQUIVALENT",
        description="CCZ gate: control symmetry CCX(0,1,2) == CCX(1,0,2)",
    ))

    # 6. Quantum Half-Adder Correct vs Buggy Ordering:
    # Correct half-adder: CCX computes Carry, CX computes Sum:
    # CCX(0,1,2) then CX(0,1)
    # Buggy half-adder: CX(0,1) then CCX(0,1,2) (corrupts input to carry!)
    tests.append(make_instance(
        "novel_half_adder_ordering_bug_nonequiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="ccx q[0], q[1], q[2];\ncx q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\nccx q[0], q[1], q[2];\n",
        expected_decision="NON_EQUIVALENT",
        description="Quantum Half-Adder: detects carry-sum gate order dependency bug",
    ))

    # 7. Quantum Teleportation Alice Kernel:
    # Bell basis measurement transformation: CX(0,1) followed by H(0)
    # Reversing order is NOT equivalent
    tests.append(make_instance(
        "novel_teleportation_alice_order_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\nh q[0];\n",
        circuit_b_body="h q[0];\ncx q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Teleportation kernel: CX then H vs H then CX are non-equivalent",
    ))

    # 8. 2-Qubit Grover Diffusion Operator:
    # Circuit A: H(0) H(1) X(0) X(1) CZ(0,1) X(0) X(1) H(0) H(1)
    # Circuit B: H(0) H(1) X(0) X(1) H(1) CX(0,1) H(1) X(0) X(1) H(0) H(1)
    # (Synthesizes CZ via H-CX-H inside the Grover diffusion loop)
    tests.append(make_instance(
        "novel_grover_diffusion_cz_decomp_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body=(
            "h q[0];\nh q[1];\n"
            "x q[0];\nx q[1];\n"
            "cz q[0], q[1];\n"
            "x q[0];\nx q[1];\n"
            "h q[0];\nh q[1];\n"
        ),
        circuit_b_body=(
            "h q[0];\nh q[1];\n"
            "x q[0];\nx q[1];\n"
            "h q[1];\ncx q[0], q[1];\nh q[1];\n"
            "x q[0];\nx q[1];\n"
            "h q[0];\nh q[1];\n"
        ),
        expected_decision="EQUIVALENT",
        description="2-qubit Grover Diffusion Operator: direct CZ vs H-CX-H decomposition",
    ))

    # 9. Pauli Commutation Anti-Symmetry (XZ = -ZX):
    # Under exact_unitary: XZ != ZX
    tests.append(make_instance(
        "novel_pauli_xz_vs_zx_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="x q[0];\nz q[0];\n",
        circuit_b_body="z q[0];\nx q[0];\n",
        expected_decision="NON_EQUIVALENT",
        description="Pauli anti-commutation XZ != ZX in exact_unitary mode",
    ))

    # 10. Pauli Commutation Anti-Symmetry (XZ = -ZX):
    # Under global_phase_unitary: XZ == ZX (they differ by factor of -1 = e^(i*pi))
    tests.append(make_instance(
        "novel_pauli_xz_vs_zx_phase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body="x q[0];\nz q[0];\n",
        circuit_b_body="z q[0];\nx q[0];\n",
        expected_decision="EQUIVALENT",
        description="Pauli anti-commutation XZ == ZX in global_phase_unitary mode (phase -1)",
    ))

    # 11. Quantum Swap Network Identity:
    # 3 CNOTs form a SWAP: CX(0,1) CX(1,0) CX(0,1) == SWAP(0,1)
    tests.append(make_instance(
        "novel_swap_from_three_cnot_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[1], q[0];\ncx q[0], q[1];\n",
        circuit_b_body="swap q[0], q[1];\n",
        expected_decision="EQUIVALENT",
        description="3-CNOT alternating chain is identically a SWAP gate",
    ))

    # 12. Quantum Swap Network Bug:
    # 2 CNOTs do NOT form a SWAP (leaving out the third CNOT):
    tests.append(make_instance(
        "novel_swap_two_cnot_bug_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[1], q[0];\n",
        circuit_b_body="swap q[0], q[1];\n",
        expected_decision="NON_EQUIVALENT",
        description="Incomplete SWAP network (2 CNOTs instead of 3) is NON_EQUIVALENT",
    ))

    # Write manifest and answer key
    inst_ids = [t["instance_id"] for t in tests]
    manifest = {
        "dataset_id": "novel_circuits_v1",
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
    print("=" * 80)
    print("  NOVEL QUANTUM ALGORITHM & CIRCUIT EQUIVALENCE TEST SUITE")
    print("=" * 80)
    tests = build_novel_dataset()
    print(f"Generated {len(tests)} novel algorithm test instances in {DATASET_DIR}\n")

    python_exe = sys.executable
    solver_script = ROOT / "submission" / "run.py"

    passed = 0
    failed = 0
    results_detail = []

    print(f"{'#':<3} {'Instance ID':<45} {'Mode':<15} {'Expected':<14} {'Actual':<14} {'Result'}")
    print("-" * 100)

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

        print(f"{idx:<3} {inst_id:<45} {t['mode']:<15} {expected:<14} {actual:<14} {status_sym}")

    total_elapsed = time.perf_counter() - total_start

    print("-" * 100)
    print(f"RESULTS: {passed}/{len(tests)} Passed (Accuracy: {passed / len(tests) * 100:.1f}%) in {total_elapsed:.2f}s")
    print("=" * 80)

    report_file = ROOT / "novel_circuits_test_report.json"
    report_data = {
        "total": len(tests),
        "passed": passed,
        "failed": failed,
        "accuracy": passed / len(tests),
        "elapsed_seconds": round(total_elapsed, 3),
        "tests": results_detail,
    }
    report_file.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    print(f"Detailed novel algorithm report saved to {report_file}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
