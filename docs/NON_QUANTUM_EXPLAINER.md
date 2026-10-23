# Quantum Circuit Equivalence: The Non-Quantum User's Guide

> **"If you can understand how a compiler optimizes a computer program without changing what it does, you can understand quantum circuit equivalence."**

---

## 1. Introduction: What is This Project?

Imagine you write a software program in Python. A smart compiler takes your code and rearranges instructions, combines steps, and removes duplicate lines to make it run 10 times faster. 

Before deploying that program to an airplane or hospital, you must ask one critical question:
> **Did the compiler's optimizations accidentally change what the program computes?**

In classical software, we call this **program verification**.
In the quantum realm, this is called **Quantum Circuit Equivalence Verification**.

This repository contains a high-performance, self-contained verification engine that takes two quantum circuits written in OpenQASM (the standard quantum assembly language) and mathematically proves whether they do the **exact same thing** under all possible circumstances.

---

## 2. Classical Computing vs. Quantum Computing (In Plain English)

To understand what quantum circuits do, you only need three intuitive concepts:

### Concept A: Bits vs. Qubits

```
Classical Bit:        [ OFF (0) ]   OR   [ ON (1) ]       (Like a light switch)
                                      
Quantum Qubit:        |ψ⟩ = α|0⟩ + β|1⟩                    (Like a spinning coin)
```

- A **classical bit** is always definitely `0` or definitely `1`.
- A **qubit** can be `0`, `1`, or a **superposition** of both at the same time. Think of a coin spinning on a table: while spinning, it is a blend of Heads and Tails until it lands.
- The numbers $\alpha$ and $\beta$ are called **amplitudes**. When squared, they give the probability of measuring 0 or 1.

### Concept B: Phase (The Invisible Clock Hand)

Unlike classical probabilities (which are just positive percentages like 50%), quantum amplitudes are **complex numbers** (they have both a magnitude and an angle).

Imagine every qubit has a tiny clock hand attached to it:
- Two waves whose clock hands point in the same direction add together (**constructive interference**).
- Two waves whose clock hands point in opposite directions cancel each other out (**destructive interference**).

Quantum algorithms work by choreographing gates so that wrong answers cancel out and right answers amplify!

---

## 3. What is a Quantum Circuit?

A quantum circuit is read like a musical score from left to right:

```
          Time Step 1    Time Step 2    Time Step 3
              │              │              │
q[0] ─────────[ H ]──────────●──────────────[ Z ]────
                             │
q[1] ────────────────────────X───────────────────────
```

- **Horizontal Lines ("Wires")**: Represent qubits traveling forward in time.
- **Boxes and Symbols ("Gates")**: Operations applied to the qubits:
  - `[ H ]` (Hadamard gate): Puts qubit 0 into a 50/50 superposition.
  - `●───X` (CNOT gate): If qubit 0 is 1, it flips qubit 1 (entangling them!).
  - `[ Z ]` (Z gate): Flips the phase (clock hand) of qubit 0.

---

## 4. Why Compare Two Circuits? (The Equivalence Problem)

On real quantum computers (like IBM Quantum, Google Sycamore, or Rigetti), qubits are extremely fragile. Heat, cosmic rays, and electrical noise cause errors ("decoherence"). 

Therefore, quantum compilers perform heavy optimizations:
1. **Gate Cancellation**: If two $X$ gates occur in a row, they cancel out ($X \cdot X = I$).
2. **Identity Substitution**: Replacing a slow 15-gate block with a faster 3-gate equivalent block.
3. **Hardware Mapping**: Rearranging gates so they only connect adjacent physical qubits on a chip.

Because quantum states cannot be copied or inspected mid-flight without destroying them (the **No-Cloning Theorem**), we cannot simply "print variable `x`" with a debugger.

**We must verify circuit equivalence mathematically before sending circuits to quantum hardware.**

---

## 5. The Two Rules of Equivalence

In our solver, each problem specifies one of two semantic modes:

### Mode 1: `exact_unitary` (Strict Mathematical Match)
In this mode, two circuits are equivalent **if and only if** their mathematical transformation matrices $U_A$ and $U_B$ are identical in every single entry:

$$U_A = U_B \quad (\text{within numerical tolerance } 10^{-9})$$

### Mode 2: `global_phase_unitary` (Physical Observational Match)
In quantum mechanics, if you multiply an entire quantum system by a constant phase factor $e^{i\phi}$ (spinning every clock hand in the universe by the exact same angle $\phi$), **no physical measurement can ever detect the difference**. The probabilities of measuring 0 or 1 remain completely unchanged.

Therefore, under `global_phase_unitary`:

$$U_B = e^{i\phi} U_A$$

Two circuits are declared `EQUIVALENT` if they perform the identical physical computation, even if their internal phase representation is shifted by an unobservable global angle.

---

## 6. The Quantum Gate Zoo

Here is a quick cheat sheet for the gates supported in this project:

| Gate | Name | What it Does in Plain English | Classical Equivalent |
|---|---|---|---|
| `i` | Identity | Does nothing; leaves qubit unchanged | `pass` / `noop` |
| `x` | Pauli-X | Swaps 0 to 1 and 1 to 0 | NOT gate |
| `y` | Pauli-Y | Bit-flip AND phase-flip combined | NOT + Phase |
| `z` | Pauli-Z | Leaves 0 alone; flips phase of 1 | Sign flip on 1 |
| `h` | Hadamard | Converts definite 0 or 1 into an even superposition | "Coin flip" |
| `s`, `sdg` | S / S-Dagger | Quarter-turn phase rotation ($90^\circ$ and $-90^\circ$) | Quarter turn |
| `t`, `tdg` | T / T-Dagger | Eighth-turn phase rotation ($45^\circ$ and $-45^\circ$) | Eighth turn |
| `sx`, `sxdg` | Sqrt-X | "Half-way NOT gate": applying two `sx` gates equals one `x` | $\sqrt{\text{NOT}}$ |
| `p(λ)`, `u1` | Phase Gate | Rotates the phase of state 1 by angle $\lambda$ radians | Arbitrary turn |
| `rx(θ)` | Rotation-X | Rotates qubit around the X-axis of the Bloch sphere | 3D X-rotation |
| `ry(θ)` | Rotation-Y | Rotates qubit around the Y-axis of the Bloch sphere | 3D Y-rotation |
| `rz(θ)` | Rotation-Z | Rotates qubit around the Z-axis of the Bloch sphere | 3D Z-rotation |
| `cx` | CNOT | Controlled-NOT: flips target if control is 1 | Conditional NOT |
| `cz` | Controlled-Z | Flips sign if both qubits are 1 | Conditional phase |
| `swap` | SWAP | Swaps the quantum states of two qubits | Variable swap |
| `cy`, `ch` | Controlled-Y / H | Applies Y or H to target if control is 1 | Conditional Y/H |
| `cp(λ)` | Controlled-Phase | Adds phase $\lambda$ only if both qubits are 1 | Two-qubit phase |
| `ccx` | Toffoli | Flips target qubit if **both** controls are 1 | AND-controlled NOT |
| `cswap` | Fredkin | Swaps two target qubits if control is 1 | Controlled SWAP |

---

## 7. How Our Solver Solves This (Under The Hood)

Our solver uses a dual-engine architecture designed for 100% precision and zero external dependencies:

```
                    ┌────────────────────────┐
                    │  Two OpenQASM Circuits │
                    │   + instance.json      │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ AST-Safe QASM Parser   │
                    │ Evaluates gate angles  │
                    └───────────┬────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌─────────────────────────────┐           ┌─────────────────────────────┐
│    Method 1: Full Unitary   │           │   Method 2: Random State    │
│  Matrix Simulation (2ⁿ×2ⁿ)  │           │   Vector Verification       │
│                             │           │                             │
│ Reconstructs full matrix    │           │ Samples Haar-random vectors │
│ column-by-column.           │           │ to catch non-equivalent     │
│ Extracts global phase:      │           │ circuits instantly.         │
│    φ = argmax(U_B / U_A)    │           │ Generates counterexamples!  │
└──────────────┬──────────────┘           └──────────────┬──────────────┘
               │                                         │
               └──────────────────────┬──────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ Precise Decision Engine   │
                        │ Tolerance: ε = 10⁻⁹       │
                        │ Output: EQUIVALENT or     │
                        │         NON_EQUIVALENT    │
                        └───────────────────────────┘
```

1. **AST-Safe Parsing**: Mathematical angle expressions like `pi/2` or `3*pi/4` are safely evaluated using Python's Abstract Syntax Tree (AST), preventing arbitrary code execution attacks.
2. **In-Place State Vector Updates**: Uses bitwise index-pair arithmetic ($2^n$ state vectors) with no heavy matrix allocations.
3. **Exact Global Phase Extraction**: Uses the polar ratio of the maximum amplitude element to reliably determine the global phase difference $\phi$, verifying $|e^{i\phi}| = 1$ and $|U_B - e^{i\phi}U_A| \le 10^{-9}$.
4. **Counterexample Generation**: When two circuits are non-equivalent, the solver can provide an exact input state where their outputs disagree.

---

## 8. Summary: Why This Matters

By verifying quantum circuit equivalence, we ensure that quantum computers can run optimized, noise-resilient algorithms without silently altering scientific computations in drug discovery, materials science, and cryptography.
