#!/usr/bin/env python3
"""
Generate a comprehensive custom test dataset for the quantum circuit equivalence solver.
Creates diverse test instances covering many categories of equivalence/non-equivalence.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "custom_test_dataset"

ALLOWED_OPS = ["h", "x", "z", "cx", "rx", "ry", "rz", "s", "sdg", "t", "tdg", "i", "y", "cz", "swap"]

QASM_HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'


def make_instance(
    instance_id: str,
    qubit_count: int,
    semantic_mode: str,
    circuit_a_body: str,
    circuit_b_body: str,
    expected_decision: str,
):
    """Create a single test instance directory with all required files."""
    inst_dir = DATASET_DIR / "instances" / instance_id
    inst_dir.mkdir(parents=True, exist_ok=True)

    # instance.json
    instance_json = {
        "allowed_operations": ALLOWED_OPS,
        "circuit_a": "circuit_a.qasm",
        "circuit_b": "circuit_b.qasm",
        "instance_id": instance_id,
        "parameter_schema": {},
        "qubit_count": qubit_count,
        "resource_limits": {"tier": "custom_test"},
        "semantic_mode": semantic_mode,
    }
    (inst_dir / "instance.json").write_text(
        json.dumps(instance_json, indent=2) + "\n", encoding="utf-8"
    )

    # circuit_a.qasm
    qasm_a = QASM_HEADER + f"qubit[{qubit_count}] q;\n" + circuit_a_body
    (inst_dir / "circuit_a.qasm").write_text(qasm_a, encoding="utf-8")

    # circuit_b.qasm
    qasm_b = QASM_HEADER + f"qubit[{qubit_count}] q;\n" + circuit_b_body
    (inst_dir / "circuit_b.qasm").write_text(qasm_b, encoding="utf-8")

    return {"instance_id": instance_id, "decision": expected_decision}


def generate_all():
    """Generate all test instances and write manifest + answer key."""
    answers = []

    # =========================================================================
    # Category 1: Identity & Gate Cancellations (exact_unitary)
    # =========================================================================

    # Test 1: X·X = I (two X gates cancel)
    answers.append(make_instance(
        "test_xx_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="x q[0];\nx q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 2: Z·Z = I
    answers.append(make_instance(
        "test_zz_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="z q[0];\nz q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 3: H·H = I
    answers.append(make_instance(
        "test_hh_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nh q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 4: S·Sdg = I
    answers.append(make_instance(
        "test_s_sdg_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="s q[0];\nsdg q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 5: T·Tdg = I
    answers.append(make_instance(
        "test_t_tdg_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="t q[0];\ntdg q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 6: S·S = Z
    answers.append(make_instance(
        "test_ss_equals_z_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="s q[0];\ns q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 7: T·T = S
    answers.append(make_instance(
        "test_tt_equals_s_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="t q[0];\nt q[0];\n",
        circuit_b_body="s q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 2: Rotation Identities (exact_unitary)
    # =========================================================================

    # Test 8: Rx(π) vs X (differ by global phase -i)  => NON_EQUIVALENT in exact mode
    answers.append(make_instance(
        "test_rx_pi_vs_x_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rx({math.pi}) q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 9: Rx(π) vs X in global_phase mode => EQUIVALENT
    answers.append(make_instance(
        "test_rx_pi_vs_x_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body=f"rx({math.pi}) q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 10: Rz(π) vs Z (differ by global phase) => NON_EQUIVALENT exact
    answers.append(make_instance(
        "test_rz_pi_vs_z_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rz({math.pi}) q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 11: Rz(π) vs Z in global_phase mode => EQUIVALENT
    answers.append(make_instance(
        "test_rz_pi_vs_z_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body=f"rz({math.pi}) q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 12: Rx(2π) = -I (global phase) vs I  => NON_EQUIVALENT exact
    answers.append(make_instance(
        "test_rx_2pi_vs_identity_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rx({2 * math.pi}) q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 13: Rx(2π) vs I in global_phase mode => EQUIVALENT
    answers.append(make_instance(
        "test_rx_2pi_vs_identity_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body=f"rx({2 * math.pi}) q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 14: Rz(π/2) = S up to global phase => NON_EQUIVALENT exact
    answers.append(make_instance(
        "test_rz_pi2_vs_s_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rz({math.pi / 2}) q[0];\n",
        circuit_b_body="s q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 15: Rz(π/2) = S in global_phase mode => EQUIVALENT
    answers.append(make_instance(
        "test_rz_pi2_vs_s_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body=f"rz({math.pi / 2}) q[0];\n",
        circuit_b_body="s q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 3: Multi-Qubit Equivalences
    # =========================================================================

    # Test 16: CNOT(0,1) then CNOT(0,1) = I (CX self-inverse)
    answers.append(make_instance(
        "test_cx_cx_cancel_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 17: SWAP = 3 CNOTs
    answers.append(make_instance(
        "test_swap_3cnot_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="swap q[0], q[1];\n",
        circuit_b_body="cx q[0], q[1];\ncx q[1], q[0];\ncx q[0], q[1];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 18: CZ symmetry: CZ(0,1) = CZ(1,0)
    answers.append(make_instance(
        "test_cz_symmetric_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cz q[0], q[1];\n",
        circuit_b_body="cz q[1], q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 19: CZ = H·CX·H (CZ via HCX decomposition on target)
    answers.append(make_instance(
        "test_cz_hcxh_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cz q[0], q[1];\n",
        circuit_b_body="h q[1];\ncx q[0], q[1];\nh q[1];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 20: CX(0,1) ≠ CX(1,0) (control/target swap changes the gate)
    answers.append(make_instance(
        "test_cx_reversed_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\n",
        circuit_b_body="cx q[1], q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 21: SWAP self-inverse
    answers.append(make_instance(
        "test_swap_swap_cancel_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="swap q[0], q[1];\nswap q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 4: Structurally Similar But Non-Equivalent
    # =========================================================================

    # Test 22: H on q[0] vs H on q[1] (different qubits) => NON_EQUIVALENT
    answers.append(make_instance(
        "test_h_wrong_qubit_nonequiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\n",
        circuit_b_body="h q[1];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 23: Near-miss rotation (tiny angle difference)
    answers.append(make_instance(
        "test_nearmiss_rotation_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rz({math.pi / 4}) q[0];\n",
        circuit_b_body=f"rz({math.pi / 4 + 0.01}) q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # =========================================================================
    # Category 5: 3-Qubit Circuits
    # =========================================================================

    # Test 24: 3-qubit identity chain cancellation
    answers.append(make_instance(
        "test_3q_cancel_equiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[1], q[2];\ncx q[1], q[2];\ncx q[0], q[1];\n",
        circuit_b_body="i q[0];\ni q[1];\ni q[2];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 25: 3-qubit non-equiv (different structure)
    answers.append(make_instance(
        "test_3q_different_nonequiv",
        qubit_count=3,
        semantic_mode="exact_unitary",
        circuit_a_body="cx q[0], q[1];\ncx q[1], q[2];\n",
        circuit_b_body="cx q[0], q[2];\ncx q[1], q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # =========================================================================
    # Category 6: HZH = X identity
    # =========================================================================

    # Test 26: HZH = X
    answers.append(make_instance(
        "test_hzh_equals_x_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nz q[0];\nh q[0];\n",
        circuit_b_body="x q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 27: HXH = Z
    answers.append(make_instance(
        "test_hxh_equals_z_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nx q[0];\nh q[0];\n",
        circuit_b_body="z q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 7: Y gate identities
    # =========================================================================

    # Test 28: Y = iXZ  => Y vs X·Z differ by global phase i => NON_EQUIVALENT exact
    answers.append(make_instance(
        "test_y_vs_xz_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="y q[0];\n",
        circuit_b_body="z q[0];\nx q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 29: Y vs X·Z in global_phase mode => EQUIVALENT (since Y = iXZ)
    answers.append(make_instance(
        "test_y_vs_xz_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body="y q[0];\n",
        circuit_b_body="z q[0];\nx q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 30: Y·Y = I
    answers.append(make_instance(
        "test_yy_cancel_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="y q[0];\ny q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 8: Empty circuits / Identity
    # =========================================================================

    # Test 31: Both empty (identity) circuits
    answers.append(make_instance(
        "test_empty_circuits_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="",
        circuit_b_body="",
        expected_decision="EQUIVALENT",
    ))

    # Test 32: Empty vs I gate
    answers.append(make_instance(
        "test_empty_vs_identity_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 33: Empty vs X gate => NON_EQUIVALENT
    answers.append(make_instance(
        "test_empty_vs_x_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="",
        circuit_b_body="x q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # =========================================================================
    # Category 9: Longer gate sequences
    # =========================================================================

    # Test 34: X·Z·X·Z = I (XZ anticommute, XZXZ = -ZX·XZ = -Z²X² = -I... actually let me compute)
    # Actually: XZ = -iY, so XZXZ = (-iY)(-iY) = -Y² = -(-I) = I? No...
    # X = [[0,1],[1,0]], Z = [[1,0],[0,-1]]
    # XZ = [[0,-1],[1,0]], XZXZ = [[0,-1],[1,0]]·[[0,-1],[1,0]] = [[-1,0],[0,-1]] = -I
    # So XZXZ = -I => NON_EQUIVALENT to I in exact mode
    answers.append(make_instance(
        "test_xzxz_vs_i_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="x q[0];\nz q[0];\nx q[0];\nz q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 35: XZXZ = -I => EQUIVALENT to I in global_phase mode
    answers.append(make_instance(
        "test_xzxz_vs_i_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body="x q[0];\nz q[0];\nx q[0];\nz q[0];\n",
        circuit_b_body="i q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 10: Ry rotation identities
    # =========================================================================

    # Test 36: Ry(π) vs Y => differ by global phase => NON_EQUIVALENT exact
    # Ry(π) = [[cos(π/2), -sin(π/2)], [sin(π/2), cos(π/2)]] = [[0, -1], [1, 0]]
    # Y = [[0, -i], [i, 0]]  -- these are totally different, not even global phase!
    # Actually: Ry(π) = [[0,-1],[1,0]] and Y = [[0,-i],[i,0]]
    # Ry(π) / Y would need a scalar c such that [[0,-1],[1,0]] = c*[[0,-i],[i,0]]
    # From (0,1): -1 = c*(-i) => c = -1/(-i) = 1/i = -i
    # From (1,0): 1 = c*(i) = (-i)(i) = 1. ✓
    # So Ry(π) = -i * Y => global phase equivalent!
    answers.append(make_instance(
        "test_ry_pi_vs_y_exact_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"ry({math.pi}) q[0];\n",
        circuit_b_body="y q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # Test 37: Ry(π) vs Y in global_phase => EQUIVALENT
    answers.append(make_instance(
        "test_ry_pi_vs_y_globalphase_equiv",
        qubit_count=1,
        semantic_mode="global_phase_unitary",
        circuit_a_body=f"ry({math.pi}) q[0];\n",
        circuit_b_body="y q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Category 11: Commutation tests
    # =========================================================================

    # Test 38: On separate qubits, gates commute: H(q0)·X(q1) = X(q1)·H(q0)
    answers.append(make_instance(
        "test_separate_qubits_commute_equiv",
        qubit_count=2,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nx q[1];\n",
        circuit_b_body="x q[1];\nh q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # Test 39: On same qubit, H·X ≠ X·H
    answers.append(make_instance(
        "test_same_qubit_no_commute_nonequiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body="h q[0];\nx q[0];\n",
        circuit_b_body="x q[0];\nh q[0];\n",
        expected_decision="NON_EQUIVALENT",
    ))

    # =========================================================================
    # Category 12: Rz composition
    # =========================================================================

    # Test 40: Rz(a)·Rz(b) = Rz(a+b) (rotation composition)
    a_val = math.pi / 3
    b_val = math.pi / 5
    answers.append(make_instance(
        "test_rz_compose_equiv",
        qubit_count=1,
        semantic_mode="exact_unitary",
        circuit_a_body=f"rz({a_val}) q[0];\nrz({b_val}) q[0];\n",
        circuit_b_body=f"rz({a_val + b_val}) q[0];\n",
        expected_decision="EQUIVALENT",
    ))

    # =========================================================================
    # Write manifest and answer key
    # =========================================================================
    instance_ids = [a["instance_id"] for a in answers]

    # manifest.json
    manifest = {
        "dataset_id": "custom_test_v1",
        "instances": instance_ids,
        "label": "CUSTOM TEST SET",
        "public_answer_key": "labels/answers.json",
    }
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    (DATASET_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    # labels/answers.json
    labels_dir = DATASET_DIR / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    answers_data = {"answers": answers}
    (labels_dir / "answers.json").write_text(
        json.dumps(answers_data, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Generated {len(answers)} test instances in {DATASET_DIR}")
    for a in answers:
        print(f"  {a['instance_id']:50s} -> {a['decision']}")


if __name__ == "__main__":
    generate_all()
