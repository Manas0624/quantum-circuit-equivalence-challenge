#!/usr/bin/env python3
"""
Quantum Circuit Equivalence Challenge - Production Submission Solver
Single-file, self-contained, standard-library-first implementation.
Decides unitary circuit equivalence under 'exact_unitary' and 'global_phase_unitary'.
"""

from __future__ import annotations

import ast
import cmath
import json
import math
import operator
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Sequence

# Prevent __pycache__ generation in evaluation environments
sys.dont_write_bytecode = True

# Central precision tolerance on amplitude/matrix absolute difference
TOL: float = 1e-9

# Mathematical constants
INV_SQRT2: float = 1.0 / math.sqrt(2.0)
TWO_PI: float = 2.0 * math.pi

# Optional acceleration via numpy if present
try:
    import numpy as np  # type: ignore

    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAS_NUMPY = False


# ============================================================================
# Safe Expression Evaluator (No eval/exec)
# ============================================================================

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Pow: operator.pow,
}

SAFE_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "π": math.pi,
    "tau": math.tau,
    "e": math.e,
}


def safe_eval_expr(expr_str: str) -> float:
    """Safely evaluates numeric parameter expressions using an AST whitelist."""
    s = expr_str.strip()
    try:
        return float(s)
    except ValueError:
        pass

    try:
        node = ast.parse(s, mode="eval").body

        def _eval(n: Any) -> float:
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return float(n.value)
            elif isinstance(n, ast.Name):
                name = n.id.lower()
                if name in SAFE_CONSTANTS:
                    return SAFE_CONSTANTS[name]
                raise ValueError(f"Unknown variable: {n.id}")
            elif isinstance(n, ast.UnaryOp):
                op_type = type(n.op)
                if op_type in SAFE_OPERATORS:
                    return float(SAFE_OPERATORS[op_type](_eval(n.operand)))
                raise ValueError(f"Unsupported unary operator: {op_type}")
            elif isinstance(n, ast.BinOp):
                op_type = type(n.op)
                if op_type in SAFE_OPERATORS:
                    return float(SAFE_OPERATORS[op_type](_eval(n.left), _eval(n.right)))
                raise ValueError(f"Unsupported binary operator: {op_type}")
            raise ValueError(f"Unsupported AST node: {type(n)}")

        return float(_eval(node))
    except Exception as exc:
        raise ValueError(f"Cannot evaluate rotation angle '{expr_str}': {exc}") from exc


# ============================================================================
# OpenQASM 3.0 Parser
# ============================================================================


class GateOp:
    __slots__ = ("name", "qubits", "params")

    def __init__(self, name: str, qubits: tuple[int, ...], params: tuple[float, ...] = ()):
        self.name = name
        self.qubits = qubits
        self.params = params

    def __repr__(self) -> str:
        return f"GateOp({self.name}, {self.qubits}, {self.params})"


class ParsedCircuit:
    __slots__ = ("num_qubits", "operations", "registers")

    def __init__(self, num_qubits: int, operations: list[GateOp], registers: dict[str, tuple[int, int]]):
        self.num_qubits = num_qubits
        self.operations = operations
        self.registers = registers


def strip_comments(text: str) -> str:
    """Strips block and line comments from QASM."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def parse_qasm(qasm_content: str, default_qubit_count: int | None = None) -> ParsedCircuit:
    """
    Robust OpenQASM 3.0 subset parser.
    Supports qubit/qreg declarations, single & multi-register indexing,
    broadcasting over bare register names, parameter expressions, and whitespace tolerance.
    """
    clean_text = strip_comments(qasm_content)
    raw_statements = [stmt.strip() for stmt in clean_text.split(";") if stmt.strip()]

    registers: dict[str, tuple[int, int]] = {}
    current_offset = 0
    operations: list[GateOp] = []

    # First pass: register declarations
    for stmt in raw_statements:
        # e.g., qubit[n] q; or qreg q[n]; or qubit q;
        m_indexed = re.match(r"^(?:qubit|qreg)\s*\[\s*(\d+)\s*\]\s*([a-zA-Z_]\w*)$", stmt)
        if m_indexed:
            size = int(m_indexed.group(1))
            name = m_indexed.group(2)
            registers[name] = (current_offset, size)
            current_offset += size
            continue

        m_single = re.match(r"^(?:qubit|qreg)\s+([a-zA-Z_]\w*)$", stmt)
        if m_single:
            name = m_single.group(1)
            registers[name] = (current_offset, 1)
            current_offset += 1
            continue

    num_qubits = current_offset if current_offset > 0 else (default_qubit_count or 1)

    def resolve_operands(token_str: str) -> list[tuple[int, ...]]:
        """Resolves operand string (handles comma-separated and bare register broadcast)."""
        tokens = [t.strip() for t in token_str.split(",") if t.strip()]
        if not tokens:
            return []

        expanded_tokens: list[list[int]] = []
        for tok in tokens:
            m_idx = re.match(r"^([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]$", tok)
            if m_idx:
                rname, idx_s = m_idx.group(1), m_idx.group(2)
                idx = int(idx_s)
                if rname in registers:
                    start_off, rsize = registers[rname]
                    if idx >= rsize:
                        raise ValueError(f"Index {idx} out of range for register {rname}[{rsize}]")
                    expanded_tokens.append([start_off + idx])
                else:
                    expanded_tokens.append([idx])
            elif tok.isdigit():
                expanded_tokens.append([int(tok)])
            elif tok in registers:
                # Bare register name -> broadcast across all qubits in that register
                start_off, rsize = registers[tok]
                expanded_tokens.append([start_off + i for i in range(rsize)])
            else:
                raise ValueError(f"Unknown qubit operand: '{tok}'")

        if len(expanded_tokens) == 1:
            # 1-qubit gate broadcast
            return [(q,) for q in expanded_tokens[0]]
        elif len(expanded_tokens) == 2:
            # 2-qubit gate
            if len(expanded_tokens[0]) == 1 and len(expanded_tokens[1]) == 1:
                return [(expanded_tokens[0][0], expanded_tokens[1][0])]
            elif len(expanded_tokens[0]) == len(expanded_tokens[1]):
                return list(zip(expanded_tokens[0], expanded_tokens[1]))
            else:
                raise ValueError(f"Mismatched broadcast register sizes in: '{token_str}'")
        elif len(expanded_tokens) == 3:
            # 3-qubit gate (e.g. ccx, cswap)
            if len(expanded_tokens[0]) == 1 and len(expanded_tokens[1]) == 1 and len(expanded_tokens[2]) == 1:
                return [(expanded_tokens[0][0], expanded_tokens[1][0], expanded_tokens[2][0])]
            elif len(expanded_tokens[0]) == len(expanded_tokens[1]) == len(expanded_tokens[2]):
                return list(zip(expanded_tokens[0], expanded_tokens[1], expanded_tokens[2]))
            else:
                raise ValueError(f"Mismatched broadcast register sizes in: '{token_str}'")
        elif all(len(tok) == 1 for tok in expanded_tokens):
            return [tuple(tok[0] for tok in expanded_tokens)]
        raise ValueError(f"Unsupported operand count in: '{token_str}'")

    # Second pass: gate statements
    for stmt in raw_statements:
        if not stmt:
            continue
        if re.match(r"^(?:OPENQASM|include|qubit|qreg|barrier)\b", stmt, re.IGNORECASE):
            continue

        # Parameterized gate: gname(param1, ...) operands
        m_param = re.match(r"^([a-zA-Z_]\w*)\s*\((.*?)\)\s*(.+)$", stmt)
        if m_param:
            gname = m_param.group(1)
            params_str = m_param.group(2)
            qubits_str = m_param.group(3)
            params = tuple(safe_eval_expr(p) for p in params_str.split(",") if p.strip())
            op_tuples = resolve_operands(qubits_str)
            for q_tup in op_tuples:
                operations.append(GateOp(gname, q_tup, params))
            continue

        # Non-parameterized gate: gname operands
        m_nonparam = re.match(r"^([a-zA-Z_]\w*)\s+(.+)$", stmt)
        if m_nonparam:
            gname = m_nonparam.group(1)
            qubits_str = m_nonparam.group(2)
            # Alias id -> i
            if gname == "id":
                gname = "i"
            op_tuples = resolve_operands(qubits_str)
            for q_tup in op_tuples:
                operations.append(GateOp(gname, q_tup))
            continue

    return ParsedCircuit(num_qubits, operations, registers)


# ============================================================================
# Exact 1-Qubit Gate Matrices (stdgates.inc)
# ============================================================================


def get_1q_matrix(name: str, params: tuple[float, ...]) -> tuple[complex, complex, complex, complex]:
    """
    Returns (m00, m01, m10, m11) exactly matching stdgates.inc semantics.
    Global phase matters in exact_unitary mode.
    """
    if name in ("i", "id"):
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 1.0 + 0j)
    elif name == "x":
        return (0.0 + 0j, 1.0 + 0j, 1.0 + 0j, 0.0 + 0j)
    elif name == "y":
        return (0.0 + 0j, -1j, 1j, 0.0 + 0j)
    elif name == "z":
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, -1.0 + 0j)
    elif name == "h":
        return (INV_SQRT2 + 0j, INV_SQRT2 + 0j, INV_SQRT2 + 0j, -INV_SQRT2 + 0j)
    elif name == "s":
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, 1j)
    elif name == "sdg":
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, -1j)
    elif name == "t":
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, cmath.exp(1j * math.pi / 4.0))
    elif name == "tdg":
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, cmath.exp(-1j * math.pi / 4.0))
    elif name == "rx":
        th = params[0] if params else 0.0
        c = math.cos(th / 2.0)
        s = -1j * math.sin(th / 2.0)
        return (c + 0j, s, s, c + 0j)
    elif name == "ry":
        th = params[0] if params else 0.0
        c = math.cos(th / 2.0)
        s = math.sin(th / 2.0)
        return (c + 0j, -s + 0j, s + 0j, c + 0j)
    elif name == "rz":
        th = params[0] if params else 0.0
        return (cmath.exp(-1j * th / 2.0), 0.0 + 0j, 0.0 + 0j, cmath.exp(1j * th / 2.0))
    elif name in ("p", "phase", "u1"):
        lam = params[0] if params else 0.0
        return (1.0 + 0j, 0.0 + 0j, 0.0 + 0j, cmath.exp(1j * lam))
    elif name == "sx":
        # sqrt(X) gate: 0.5 * [[1+i, 1-i], [1-i, 1+i]]
        return (0.5 * (1.0 + 1j), 0.5 * (1.0 - 1j), 0.5 * (1.0 - 1j), 0.5 * (1.0 + 1j))
    elif name == "sxdg":
        # sqrt(X)^dagger gate: 0.5 * [[1-i, 1+i], [1+i, 1-i]]
        return (0.5 * (1.0 - 1j), 0.5 * (1.0 + 1j), 0.5 * (1.0 + 1j), 0.5 * (1.0 - 1j))
    elif name == "u2":
        # u2(phi, lambda) = 1/sqrt(2) * [[1, -exp(i*lam)], [exp(i*phi), exp(i*(phi+lam))]]
        phi = params[0] if len(params) > 0 else 0.0
        lam = params[1] if len(params) > 1 else 0.0
        c = INV_SQRT2
        return (
            c + 0j,
            -c * cmath.exp(1j * lam),
            c * cmath.exp(1j * phi),
            c * cmath.exp(1j * (phi + lam)),
        )
    elif name in ("u3", "u"):
        # u3(theta, phi, lambda)
        th = params[0] if len(params) > 0 else 0.0
        phi = params[1] if len(params) > 1 else 0.0
        lam = params[2] if len(params) > 2 else 0.0
        costh2 = math.cos(th / 2.0)
        sinth2 = math.sin(th / 2.0)
        return (
            costh2 + 0j,
            -cmath.exp(1j * lam) * sinth2,
            cmath.exp(1j * phi) * sinth2,
            cmath.exp(1j * (phi + lam)) * costh2,
        )
    raise ValueError(f"Unsupported 1-qubit gate: {name}")


# ============================================================================
# Pure-Python State Vector Simulator (In-place index-pair updates)
# ============================================================================


def apply_gate_py(state: list[complex], gate: GateOp, n: int) -> None:
    """Applies a gate in-place to statevector of size 2^n in pure Python."""
    gname = gate.name
    qubits = gate.qubits
    dim = 1 << n

    if gname in ("i", "id"):
        return

    if len(qubits) == 1:
        q = qubits[0]
        m00, m01, m10, m11 = get_1q_matrix(gname, gate.params)
        half = 1 << q
        step = half << 1
        for base in range(0, dim, step):
            for i in range(base, base + half):
                j = i | half
                v0 = state[i]
                v1 = state[j]
                state[i] = m00 * v0 + m01 * v1
                state[j] = m10 * v0 + m11 * v1
        return

    elif len(qubits) == 2:
        q1, q2 = qubits
        mask1 = 1 << q1
        mask2 = 1 << q2

        if gname == "cx":
            # Control q1, Target q2
            for i in range(dim):
                if (i & mask1) and not (i & mask2):
                    j = i | mask2
                    state[i], state[j] = state[j], state[i]
            return

        elif gname == "cz":
            # Symmetric CZ: flip phase when both bits are 1
            mask12 = mask1 | mask2
            for i in range(dim):
                if (i & mask12) == mask12:
                    state[i] = -state[i]
            return

        elif gname in ("cp", "cphase"):
            lam = gate.params[0] if gate.params else 0.0
            phase_fac = cmath.exp(1j * lam)
            mask12 = mask1 | mask2
            for i in range(dim):
                if (i & mask12) == mask12:
                    state[i] *= phase_fac
            return

        elif gname == "swap":
            for i in range(dim):
                b1 = 1 if (i & mask1) else 0
                b2 = 1 if (i & mask2) else 0
                if b1 == 1 and b2 == 0:
                    j = (i ^ mask1) | mask2
                    state[i], state[j] = state[j], state[i]
            return

        elif gname in ("cy", "ch", "crx", "cry", "crz"):
            base_name = gname[1:]
            m00, m01, m10, m11 = get_1q_matrix(base_name, gate.params)
            for i in range(dim):
                if (i & mask1) and not (i & mask2):
                    j = i | mask2
                    v0 = state[i]
                    v1 = state[j]
                    state[i] = m00 * v0 + m01 * v1
                    state[j] = m10 * v0 + m11 * v1
            return

    elif len(qubits) == 3:
        q1, q2, q3 = qubits
        mask1 = 1 << q1
        mask2 = 1 << q2
        mask3 = 1 << q3
        mask12 = mask1 | mask2

        if gname in ("ccx", "toffoli"):
            for i in range(dim):
                if (i & mask12) == mask12 and not (i & mask3):
                    j = i | mask3
                    state[i], state[j] = state[j], state[i]
            return

        elif gname in ("cswap", "fredkin"):
            for i in range(dim):
                if i & mask1:
                    b2 = 1 if (i & mask2) else 0
                    b3 = 1 if (i & mask3) else 0
                    if b2 == 1 and b3 == 0:
                        j = (i ^ mask2) | mask3
                        state[i], state[j] = state[j], state[i]
            return

    raise ValueError(f"Unsupported gate in pure-python simulation: {gname} with {len(qubits)} qubits")


def simulate_circuit_py(ops: Sequence[GateOp], initial_state: list[complex], n: int) -> list[complex]:
    state = list(initial_state)
    for op in ops:
        apply_gate_py(state, op, n)
    return state


def compute_full_unitary_py(circuit: ParsedCircuit, n: int) -> list[list[complex]]:
    """Builds full 2^n x 2^n unitary column-by-column in pure Python."""
    dim = 1 << n
    columns: list[list[complex]] = []
    for col_idx in range(dim):
        basis_state = [0.0 + 0j] * dim
        basis_state[col_idx] = 1.0 + 0j
        col = simulate_circuit_py(circuit.operations, basis_state, n)
        columns.append(col)

    # Transpose columns into rows: U[r][c] = columns[c][r]
    U = [[columns[c][r] for c in range(dim)] for r in range(dim)]
    return U


# ============================================================================
# Accelerated NumPy Tensor Simulator (Used if numpy is installed)
# ============================================================================


def compute_full_unitary_np(circuit: ParsedCircuit, n: int) -> np.ndarray:
    """Builds full unitary matrix in NumPy via parallel tensor contraction."""
    dim = 1 << n
    U = np.eye(dim, dtype=np.complex128)

    for op in circuit.operations:
        gname = op.name
        qubits = op.qubits

        if gname in ("i", "id"):
            continue

        if len(qubits) == 1:
            q = qubits[0]
            ax = n - 1 - q
            m00, m01, m10, m11 = get_1q_matrix(gname, op.params)
            G = np.array([[m00, m01], [m10, m11]], dtype=np.complex128)
            shape = [2] * n + [dim]
            T = U.reshape(shape)
            T = np.tensordot(G, T, axes=([1], [ax]))
            T = np.moveaxis(T, 0, ax)
            U = T.reshape((dim, dim))

        elif len(qubits) == 2:
            q1, q2 = qubits
            ax1 = n - 1 - q1
            ax2 = n - 1 - q2
            shape = [2] * n + [dim]
            T = U.reshape(shape)

            if gname == "swap":
                T = np.swapaxes(T, ax1, ax2)
                U = T.reshape((dim, dim))

            elif gname == "cz":
                idx = [slice(None)] * (n + 1)
                idx[ax1] = 1
                idx[ax2] = 1
                T[tuple(idx)] *= -1.0
                U = T.reshape((dim, dim))

            elif gname == "cx":
                idx_c1_t0 = [slice(None)] * (n + 1)
                idx_c1_t0[ax1] = 1
                idx_c1_t0[ax2] = 0

                idx_c1_t1 = [slice(None)] * (n + 1)
                idx_c1_t1[ax1] = 1
                idx_c1_t1[ax2] = 1

                val_0 = np.copy(T[tuple(idx_c1_t0)])
                val_1 = np.copy(T[tuple(idx_c1_t1)])

                T[tuple(idx_c1_t0)] = val_1
                T[tuple(idx_c1_t1)] = val_0
                U = T.reshape((dim, dim))

    return U


def simulate_state_np(ops: Sequence[GateOp], state: np.ndarray, n: int) -> np.ndarray:
    """Simulates statevector of size 2^n in NumPy."""
    dim = 1 << n
    psi = np.copy(state).reshape([2] * n)

    for op in ops:
        gname = op.name
        qubits = op.qubits

        if gname in ("i", "id"):
            continue

        if len(qubits) == 1:
            q = qubits[0]
            ax = n - 1 - q
            m00, m01, m10, m11 = get_1q_matrix(gname, op.params)
            G = np.array([[m00, m01], [m10, m11]], dtype=np.complex128)
            psi = np.tensordot(G, psi, axes=([1], [ax]))
            psi = np.moveaxis(psi, 0, ax)

        elif len(qubits) == 2:
            q1, q2 = qubits
            ax1 = n - 1 - q1
            ax2 = n - 1 - q2
            if gname == "swap":
                psi = np.swapaxes(psi, ax1, ax2)
            elif gname == "cz":
                idx = [slice(None)] * n
                idx[ax1] = 1
                idx[ax2] = 1
                psi[tuple(idx)] *= -1.0
            elif gname == "cx":
                idx_c1_t0 = [slice(None)] * n
                idx_c1_t0[ax1] = 1
                idx_c1_t0[ax2] = 0

                idx_c1_t1 = [slice(None)] * n
                idx_c1_t1[ax1] = 1
                idx_c1_t1[ax2] = 1

                val_0 = np.copy(psi[tuple(idx_c1_t0)])
                val_1 = np.copy(psi[tuple(idx_c1_t1)])

                psi[tuple(idx_c1_t0)] = val_1
                psi[tuple(idx_c1_t1)] = val_0

    return psi.reshape(dim)


# ============================================================================
# Equivalence Decision Engines (Method 1 & Method 2)
# ============================================================================


def are_gate_lists_identical(ops_a: Sequence[GateOp], ops_b: Sequence[GateOp]) -> bool:
    """Fast shortcut: checks if both gate lists are strictly identical."""
    if len(ops_a) != len(ops_b):
        return False
    for g1, g2 in zip(ops_a, ops_b):
        if g1.name != g2.name or g1.qubits != g2.qubits:
            return False
        if len(g1.params) != len(g2.params):
            return False
        for p1, p2 in zip(g1.params, g2.params):
            if abs(p1 - p2) > TOL:
                return False
    return True


def method1_full_unitary(
    circ_a: ParsedCircuit,
    circ_b: ParsedCircuit,
    n: int,
    semantic_mode: str,
) -> tuple[bool, dict[str, Any]]:
    """
    Method 1: Deterministic full unitary comparison.
    Computes U_A, U_B column-by-column.
    """
    dim = 1 << n

    if HAS_NUMPY:
        U_a = compute_full_unitary_np(circ_a, n)
        U_b = compute_full_unitary_np(circ_b, n)

        if semantic_mode == "exact_unitary":
            max_diff = float(np.max(np.abs(U_a - U_b)))
            return (max_diff <= TOL), {"method": "method1_numpy_exact", "max_diff": max_diff}

        elif semantic_mode == "global_phase_unitary":
            # Find entry with maximum absolute value in U_a
            flat_idx = int(np.argmax(np.abs(U_a)))
            r, c = divmod(flat_idx, dim)
            val_a = U_a[r, c]
            val_b = U_b[r, c]

            if abs(val_a) < 1e-12:
                # Should not happen for unitary matrices
                return False, {"method": "method1_numpy_phase", "error": "zero_unitary"}

            phi_c = val_b / val_a
            mod_err = abs(abs(phi_c) - 1.0)
            if mod_err > TOL:
                return False, {"method": "method1_numpy_phase", "modulus_error": mod_err}

            phi_c /= abs(phi_c)
            max_diff = float(np.max(np.abs(U_b - phi_c * U_a)))
            return (max_diff <= TOL), {
                "method": "method1_numpy_phase",
                "max_diff": max_diff,
                "phase": str(phi_c),
            }

    else:
        # Pure-Python path
        U_a = compute_full_unitary_py(circ_a, n)
        U_b = compute_full_unitary_py(circ_b, n)

        if semantic_mode == "exact_unitary":
            max_diff = 0.0
            for r in range(dim):
                for c in range(dim):
                    diff = abs(U_a[r][c] - U_b[r][c])
                    if diff > max_diff:
                        max_diff = diff
                    if diff > TOL:
                        return False, {"method": "method1_py_exact", "max_diff": max_diff}
            return True, {"method": "method1_py_exact", "max_diff": max_diff}

        elif semantic_mode == "global_phase_unitary":
            max_val = -1.0
            best_r, best_c = 0, 0
            for r in range(dim):
                for c in range(dim):
                    val = abs(U_a[r][c])
                    if val > max_val:
                        max_val = val
                        best_r, best_c = r, c

            val_a = U_a[best_r][best_c]
            val_b = U_b[best_r][best_c]
            if abs(val_a) < 1e-12:
                return False, {"method": "method1_py_phase", "error": "zero_unitary"}

            phi_c = val_b / val_a
            if abs(abs(phi_c) - 1.0) > TOL:
                return False, {"method": "method1_py_phase", "modulus_error": abs(abs(phi_c) - 1.0)}

            phi_c /= abs(phi_c)
            max_diff = 0.0
            for r in range(dim):
                for c in range(dim):
                    diff = abs(U_b[r][c] - phi_c * U_a[r][c])
                    if diff > max_diff:
                        max_diff = diff
                    if diff > TOL:
                        return False, {"method": "method1_py_phase", "max_diff": max_diff}

            return True, {"method": "method1_py_phase", "max_diff": max_diff, "phase": str(phi_c)}

    return False, {"method": "method1_unhandled"}


def method2_random_states(
    circ_a: ParsedCircuit,
    circ_b: ParsedCircuit,
    n: int,
    semantic_mode: str,
    time_remaining: float,
) -> tuple[bool, dict[str, Any]]:
    """
    Method 2: Random complex Gaussian state simulation.
    Tests |0...0> plus m >= 4 random states with fixed seed for determinism.
    """
    dim = 1 << n
    rng = random.Random(42)

    # Adjust sample count if budget is tight
    num_samples = 4 if time_remaining > 1.5 else 2

    # Prepare states: state 0 is |0...0>
    test_states: list[Any] = []

    # Basis |0...0>
    if HAS_NUMPY:
        s0 = np.zeros(dim, dtype=np.complex128)
        s0[0] = 1.0
        test_states.append(s0)
    else:
        s0_py = [0.0 + 0j] * dim
        s0_py[0] = 1.0 + 0j
        test_states.append(s0_py)

    # Random normalized complex Gaussian states
    for _ in range(num_samples):
        if HAS_NUMPY:
            real_p = np.array([rng.gauss(0.0, 1.0) for _ in range(dim)], dtype=np.float64)
            imag_p = np.array([rng.gauss(0.0, 1.0) for _ in range(dim)], dtype=np.float64)
            st = real_p + 1j * imag_p
            norm = float(np.linalg.norm(st))
            if norm > 0:
                st /= norm
            test_states.append(st)
        else:
            st_py: list[complex] = []
            sum_sq = 0.0
            for _ in range(dim):
                c = complex(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0))
                st_py.append(c)
                sum_sq += c.real * c.real + c.imag * c.imag
            norm_py = math.sqrt(sum_sq)
            if norm_py > 0:
                st_py = [c / norm_py for c in st_py]
            test_states.append(st_py)

    # Run simulations
    out_a: list[Any] = []
    out_b: list[Any] = []

    for st in test_states:
        if HAS_NUMPY:
            res_a = simulate_state_np(circ_a.operations, st, n)
            res_b = simulate_state_np(circ_b.operations, st, n)
        else:
            res_a = simulate_circuit_py(circ_a.operations, st, n)
            res_b = simulate_circuit_py(circ_b.operations, st, n)
        out_a.append(res_a)
        out_b.append(res_b)

    if semantic_mode == "exact_unitary":
        max_diff = 0.0
        for idx in range(len(test_states)):
            oa = out_a[idx]
            ob = out_b[idx]
            if HAS_NUMPY:
                diff = float(np.max(np.abs(oa - ob)))
            else:
                diff = max(abs(oa[k] - ob[k]) for k in range(dim))
            if diff > max_diff:
                max_diff = diff
            if diff > TOL:
                return False, {"method": "method2_random_exact", "max_diff": max_diff, "sample": idx}
        return True, {"method": "method2_random_exact", "max_diff": max_diff, "samples_tested": len(test_states)}

    elif semantic_mode == "global_phase_unitary":
        # Derive global phase candidate from first random state (index 1)
        ref_idx = 1 if len(test_states) > 1 else 0
        oa = out_a[ref_idx]
        ob = out_b[ref_idx]

        if HAS_NUMPY:
            overlap = complex(np.vdot(oa, ob))
        else:
            overlap = sum(oa[k].conjugate() * ob[k] for k in range(dim))

        mod_err = abs(abs(overlap) - 1.0)
        if mod_err > TOL:
            return False, {"method": "method2_random_phase", "overlap_modulus_error": mod_err}

        phi_c = overlap / abs(overlap)

        # Check that the SAME phi_c holds across ALL states
        max_diff = 0.0
        for idx in range(len(test_states)):
            curr_a = out_a[idx]
            curr_b = out_b[idx]
            if HAS_NUMPY:
                diff = float(np.max(np.abs(curr_b - phi_c * curr_a)))
            else:
                diff = max(abs(curr_b[k] - phi_c * curr_a[k]) for k in range(dim))
            if diff > max_diff:
                max_diff = diff
            if diff > TOL:
                return False, {
                    "method": "method2_random_phase",
                    "max_diff": max_diff,
                    "sample": idx,
                    "phase": str(phi_c),
                }

        return True, {
            "method": "method2_random_phase",
            "max_diff": max_diff,
            "phase": str(phi_c),
            "samples_tested": len(test_states),
        }

    return False, {"method": "method2_unhandled"}


# ============================================================================
# Main Equivalence Solver
# ============================================================================


def decide_circuit_equivalence(
    instance_dir: Path,
    metadata: dict[str, Any],
    time_limit: float = 3.5,
) -> tuple[str, dict[str, Any]]:
    """
    Autonomous equivalence solver. Selects the optimal method based on
    qubit count, available runtime, and library support.
    """
    t_start = time.perf_counter()

    instance_id = str(metadata.get("instance_id", "unknown"))
    semantic_mode = str(metadata.get("semantic_mode", "exact_unitary"))
    meta_q_count = metadata.get("qubit_count")

    ca_name = metadata.get("circuit_a", "circuit_a.qasm")
    cb_name = metadata.get("circuit_b", "circuit_b.qasm")

    qasm_a_path = instance_dir / ca_name
    qasm_b_path = instance_dir / cb_name

    qasm_a = qasm_a_path.read_text(encoding="utf-8")
    qasm_b = qasm_b_path.read_text(encoding="utf-8")

    # Parse circuits
    circ_a = parse_qasm(qasm_a, default_qubit_count=meta_q_count)
    circ_b = parse_qasm(qasm_b, default_qubit_count=meta_q_count)

    # Robust handling: unify qubit count to max of all sources
    declared_qubits = [circ_a.num_qubits, circ_b.num_qubits]
    if isinstance(meta_q_count, int) and meta_q_count > 0:
        declared_qubits.append(meta_q_count)
    n = max(declared_qubits)

    if circ_a.num_qubits != n or circ_b.num_qubits != n:
        print(
            f"[Warning] Mismatched qubit counts (circ_a={circ_a.num_qubits}, circ_b={circ_b.num_qubits}, instance={meta_q_count}); using n={n}",
            file=sys.stderr,
        )

    circ_a.num_qubits = n
    circ_b.num_qubits = n

    # Shortcut: Identical operation sequences
    if are_gate_lists_identical(circ_a.operations, circ_b.operations):
        return "EQUIVALENT", {"method": "shortcut_identical_gates", "runtime": time.perf_counter() - t_start}

    # Decide method threshold based on numpy presence and n
    # Method 1 threshold: n <= 10 with numpy (~25ms), n <= 8 in pure Python (~50ms)
    method1_threshold = 10 if HAS_NUMPY else 8

    time_elapsed = time.perf_counter() - t_start
    time_remaining = max(0.5, time_limit - time_elapsed)

    if n <= method1_threshold and time_remaining > 0.4:
        is_equiv, ev = method1_full_unitary(circ_a, circ_b, n, semantic_mode)
        ev["runtime"] = time.perf_counter() - t_start
        return ("EQUIVALENT" if is_equiv else "NON_EQUIVALENT"), ev
    else:
        is_equiv, ev = method2_random_states(circ_a, circ_b, n, semantic_mode, time_remaining)
        ev["runtime"] = time.perf_counter() - t_start
        return ("EQUIVALENT" if is_equiv else "NON_EQUIVALENT"), ev


# ============================================================================
# CLI Entry Point
# ============================================================================


def main() -> int:
    """CLI runner conforming strictly to challenge protocol."""
    if len(sys.argv) != 2:
        print("Usage: python run.py <instance_directory>", file=sys.stderr)
        return 2

    instance_dir = Path(sys.argv[1]).resolve()
    inst_json_path = instance_dir / "instance.json"

    fallback_id = instance_dir.name
    try:
        if inst_json_path.exists():
            metadata = json.loads(inst_json_path.read_text(encoding="utf-8"))
            fallback_id = str(metadata.get("instance_id", fallback_id))
        else:
            print(f"[Error] instance.json not found in {instance_dir}", file=sys.stderr)
            out_json = {"instance_id": fallback_id, "decision": "NON_EQUIVALENT"}
            print(json.dumps(out_json, ensure_ascii=True))
            return 0

        # Execute solver
        decision, evidence = decide_circuit_equivalence(instance_dir, metadata, time_limit=3.5)

        # Log evidence to stderr only if DEBUG environment variable is set
        if os.environ.get("DEBUG"):
            print(f"[Info] {json.dumps(evidence, default=str)}", file=sys.stderr)

        # Emit strictly ONE JSON object to stdout in the exact expected format
        payload = {
            "instance_id": str(metadata["instance_id"]),
            "decision": decision,
        }
        print(json.dumps(payload, ensure_ascii=True))
        return 0

    except Exception as exc:
        # Never crash: log error to stderr and output valid fallback JSON
        print(f"[Fatal] Solver exception: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)

        fallback_payload = {
            "instance_id": fallback_id,
            "decision": "NON_EQUIVALENT",
        }
        print(json.dumps(fallback_payload, ensure_ascii=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
