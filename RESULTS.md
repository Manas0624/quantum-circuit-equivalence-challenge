# 🏆 Verification Results: Quantum Circuit Equivalence

## Executive Summary

The production submission solver ([`submission/run.py`](submission/run.py)) has been evaluated against **five comprehensive test suites** comprising **104 distinct quantum circuit instances** across **20 categories** of quantum identities, structural pairs, gate decompositions, algorithmic building blocks, and semantic edge cases.

| Dataset | Total Instances | Correct Decisions | Accuracy | Evaluator Status | Runtime | Focus Area |
|---|---|---|---|---|---|---|
| **Official Public Dataset** | 6 | 6 | **100.0%** | ✅ `{"accuracy": 1.0, "valid": 6}` | ~1.5s | Baseline verification & protocol checks |
| **Custom Core Test Suite** | 40 | 40 | **100.0%** | ✅ `{"accuracy": 1.0, "valid": 40}` | ~9.8s | Involutions, rotations, global phase |
| **Extended Gate Test Suite** | 26 | 26 | **100.0%** | ✅ `{"accuracy": 1.0, "valid": 26}` | ~11.2s | $\sqrt{X}$, $U_3$, Toffoli, Fredkin decompositions |
| **Novel Quantum Algorithms** | 12 | 12 | **100.0%** | ✅ `{"accuracy": 1.0, "valid": 12}` | ~6.8s | Grover, CCZ, CNOT reversal, state-prep traps |
| **Structural Similar Pairs** | 20 | 20 | **100.0%** | ✅ `{"accuracy": 1.0, "valid": 20}` | ~10.4s | Paired twin circuits modeled on `dev_structural_001` |
| **Overall Grand Total** | **104** | **104** | **100.0%** | 🏆 **PERFECT ACCURACY** | **~39.7s** | Complete standard & advanced quantum validation |

---

## 🔍 Structural Similar Pairs Breakdown (Modelled on `dev_structural_001`)

Directly inspired by public benchmark instance `dev_structural_001` (where Circuit A and Circuit B have nearly identical gate topology with identity insertions), this suite presents **10 twin pairs** where one circuit is `EQUIVALENT` and the other looks almost identical but contains an adversarial "near-miss" bug (`NON_EQUIVALENT`):

| Pair Group | Focus | Equivalent Twin | Non-Equivalent Bug Twin | Result |
|---|---|---|---|---|
| **Group 1** | Middle-Circuit Z Cancellation | `struct_pair_01_zz_cancel_equiv`<br>($Z \cdot Z = I$ inserted into Bell circuit) | `struct_pair_02_single_z_bug_nonequiv`<br>(Single Z inserted, missing second Z) | ✅ Both 100% Correct |
| **Group 2** | Adjoint Dagger Omission | `struct_pair_03_s_sdg_cancel_equiv`<br>($S \cdot S^\dagger = I$ cancels cleanly) | `struct_pair_04_s_s_omitted_dagger_nonequiv`<br>($S \cdot S = Z \neq I$, omitted dagger) | ✅ Both 100% Correct |
| **Group 3** | Wire Commutation | `struct_pair_05_disjoint_commute_equiv`<br>(Reordering gates on disjoint wires) | `struct_pair_06_same_wire_reorder_nonequiv`<br>(Reordering non-commuting $H \cdot Z \neq Z \cdot H$ on same wire) | ✅ Both 100% Correct |
| **Group 4** | CNOT Control Propagation | `struct_pair_07_cnot_control_z_commute_equiv`<br>($Z$ commutes past CNOT control) | `struct_pair_08_cnot_target_z_noncommute_nonequiv`<br>($Z$ does NOT commute past CNOT target) | ✅ Both 100% Correct |
| **Group 5** | CNOT Target Propagation | `struct_pair_09_cnot_target_x_commute_equiv`<br>($X$ commutes past CNOT target) | `struct_pair_10_cnot_control_x_noncommute_nonequiv`<br>($X$ does NOT commute past CNOT control) | ✅ Both 100% Correct |
| **Group 6** | Gate Symmetry (CZ vs CX) | `struct_pair_11_cz_symmetric_equiv`<br>($CZ_{0,1} = CZ_{1,0}$ control-target symmetry) | `struct_pair_12_cx_asymmetric_nonequiv`<br>(Misconception that CNOT is symmetric: $CX_{0,1} \neq CX_{1,0}$) | ✅ Both 100% Correct |
| **Group 7** | Rotation Angle Inversion | `struct_pair_13_rx_inv_cancel_equiv`<br>($R_x(\pi/3) R_x(-\pi/3) = I$ cancels) | `struct_pair_14_rx_sign_error_nonequiv`<br>($R_x(\pi/3) R_x(\pi/3) = R_x(2\pi/3) \neq I$, sign typo) | ✅ Both 100% Correct |
| **Group 8** | Wire Index Typo | `struct_pair_15_idle_wire_padding_equiv`<br>(Explicit identity on idle wire $q[2]$) | `struct_pair_16_target_wire_typo_nonequiv`<br>(CNOT connects to wrong wire $q[2]$ instead of $q[1]$) | ✅ Both 100% Correct |
| **Group 9** | Full $2\pi$ Phase Shift | `struct_pair_17_rz_2pi_phase_equiv`<br>($R_z(2\pi) = -I$, equivalent in `global_phase_unitary`) | `struct_pair_18_rz_2pi_exact_nonequiv`<br>($-I \neq I$ non-equivalent in `exact_unitary` mode) | ✅ Both 100% Correct |
| **Group 10** | Hadamard Conjugation | `struct_pair_19_hadamard_conjugation_equiv`<br>($H \cdot X \cdot H = Z$ identity substitution) | `struct_pair_20_hadamard_conjugation_bug_nonequiv`<br>($H \cdot X \cdot H$ mistakenly replaced by $X$ instead of $Z$) | ✅ Both 100% Correct |

---

## How to Reproduce All Results

Run these commands in PowerShell or bash:

```bash
# 1. Run official public dataset evaluation (6 tests)
.venv\Scripts\python evaluator/evaluate.py --submission submission --dataset public_dataset --out public_report.json

# 2. Run custom core dataset evaluation (40 tests)
.venv\Scripts\python evaluator/evaluate.py --submission submission --dataset custom_test_dataset --out custom_report.json

# 3. Run extended gates test suite (26 tests with sx, u3, ccx, cswap)
.venv\Scripts\python tests/test_extended_gates.py
.venv\Scripts\python evaluator/evaluate.py --submission submission --dataset extended_gates_dataset --out extended_eval_report.json

# 4. Run novel quantum algorithm test suite (12 tests)
.venv\Scripts\python tests/test_novel_circuits.py
.venv\Scripts\python evaluator/evaluate.py --submission submission --dataset novel_circuits_dataset --out novel_eval_report.json

# 5. Run structural similar pairs test suite (20 tests modeled on dev_structural_001)
.venv\Scripts\python tests/test_structural_pairs.py
.venv\Scripts\python evaluator/evaluate.py --submission submission --dataset structural_pairs_dataset --out structural_eval_report.json
```
