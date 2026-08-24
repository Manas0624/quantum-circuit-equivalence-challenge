# Specification

## Instance Directory

An instance directory contains `instance.json`, `circuit_a.qasm`, and `circuit_b.qasm`.

Required `instance.json` fields:

- `instance_id`: string
- `semantic_mode`: `exact_unitary` or `global_phase_unitary`
- `qubit_count`: positive integer
- `parameter_schema`: object; empty for V1 core instances
- `allowed_operations`: supported gate names
- `resource_limits`: public resource metadata
- `circuit_a`: relative path to Circuit A
- `circuit_b`: relative path to Circuit B

## Qubit Indexing

Qubits are ordered by their integer index in the single declaration `qubit[n] q;`. Gate operands such as `q[0]` and `q[1]` refer to those indices.

## Gate Definitions

Supported one-qubit gates: `i`, `x`, `y`, `z`, `h`, `s`, `sdg`, `t`, `tdg`, `rx(theta)`, `ry(theta)`, `rz(theta)`.

Supported two-qubit gates: `cx`, `cz`, `swap`.

The gates follow the standard unitary definitions used by OpenQASM `stdgates.inc`.

## Parameter Conventions

Rotation parameters are real numeric literals in radians. Symbolic all-real parameter equivalence is not part of the V1 scored core.

## Semantic Modes

### exact_unitary

Return `EQUIVALENT` only if the circuits induce the same unitary matrix.

### global_phase_unitary

Return `EQUIVALENT` if there exists a real number `phi` such that `U_A = exp(i phi) U_B`.

Global phase is ignored only in this mode.

## Numerical Tolerance

Participants may choose numerical tolerances for their own methods. Official judging is based on the benchmark ground truth, not on participant-reported tolerances.

## Malformed Input Behavior

Official instances are intended to be well formed within the V1 subset. If a submission encounters malformed input, it should fail cleanly or emit a valid JSON decision if it can do so responsibly.

## Output Schema

Required stdout JSON:

```json
{"instance_id": "...", "decision": "EQUIVALENT" | "NON_EQUIVALENT"}
```

The `decision` value must be exactly one of:

```text
EQUIVALENT
NON_EQUIVALENT
```

Optional fields:

- `evidence`: object
- `counterexample`: object

## Resource Rules

Official-style evaluation is expected to run without network access. Time and memory limits may be enforced by the official evaluation environment. See `RULES.md` and `SUBMISSION_GUIDE.md`.
