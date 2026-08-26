# Challenge

Given two quantum circuits over the same ordered qubits, decide whether they implement the same unitary transformation under the instance's declared semantic mode.

Each instance directory contains:

```text
instance.json
circuit_a.qasm
circuit_b.qasm
```

## Input

`instance.json` names the two circuit files, the qubit count, the semantic mode, the supported operation set, and resource metadata.

## Required Output

Your program must print one JSON object with:

- `instance_id`: copied from `instance.json`
- `decision`: `EQUIVALENT` or `NON_EQUIVALENT`

The same output schema is used for public, validation, and official-style instances. `evidence` and `counterexample` may be included as optional JSON objects for diagnostics, but they do not change scoring.

## Equivalence Semantics

- `exact_unitary`: equivalent only when Circuit A and Circuit B induce the same unitary matrix.
- `global_phase_unitary`: equivalent when the induced unitary matrices differ by a scalar global phase.

## Supported QASM Subset

V1 uses OpenQASM 3.0 with `stdgates.inc`, one qubit declaration, and unitary gates from the supported set in `SPECIFICATION.md`.

## Parameter Rules

Numeric rotation literals may appear for `rx`, `ry`, and `rz`. Symbolic all-real parameter equivalence is out of scope for the V1 scored core.

## Out Of Scope

Measurements, resets, classical control, noise models, pulse schedules, hardware topology, calibration data, cloud quantum hardware behavior, and proprietary runtime behavior are out of scope.

## Allowed Approaches

Participants may build simulators, canonicalizers, symbolic tools, randomized/state-based checkers, hybrid systems, or other lawful verification systems.

## Valid Submission

A valid submission follows the command and JSON protocol in `SUBMISSION_GUIDE.md`, uses only permitted resources during evaluation, and does not attempt to access hidden data or tamper with benchmarks.

Validation data does not require a different submission format. Public development labels are included for local scoring; validation labels are not included publicly.
