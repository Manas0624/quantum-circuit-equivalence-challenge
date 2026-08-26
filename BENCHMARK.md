# Benchmark Overview

Quantum Circuit Equivalence Challenge is a public challenge package for black-box verification of quantum circuit equivalence. Participants receive pairs of OpenQASM circuits and decide whether each pair implements the same unitary transformation under the semantic mode declared by the instance.

This document is a benchmark-facing overview for researchers, educators, and future users. It is not a research paper.

## Problem

Quantum circuit equivalence asks whether two circuit descriptions have the same semantics, not merely whether they look similar. Two circuits can use different gate sequences and still implement the same transformation. Conversely, circuits that look structurally similar can differ semantically because of gate order, controls, phases, rotations, or qubit interactions.

The challenge asks participants to build a program that reads an instance directory containing `instance.json`, `circuit_a.qasm`, and `circuit_b.qasm`, then emits one JSON decision for that instance.

## Equivalence Modes

The V1 specification includes two unitary equivalence modes:

- `exact_unitary`: return `EQUIVALENT` only when Circuit A and Circuit B induce the same unitary matrix.
- `global_phase_unitary`: return `EQUIVALENT` when the induced unitaries differ only by a scalar global phase.

The active semantic mode is declared in each instance's `instance.json`.

## Structural Versus Semantic Equivalence

Syntactic or structural comparison can be useful, but it is not sufficient for the challenge. A successful solver should reason about the transformation implemented by the circuits. Participants may use exact simulation, state-based checks, canonicalization, symbolic methods, randomized testing, hybrid strategies, or other lawful techniques.

## Datasets

`public_dataset` is a small public development set. It includes public labels through `public_answer_key`, so participants can locally verify that their submission protocol works and see development-set correctness.

`validation_dataset` is an unlabeled validation-style set. It uses exactly the same participant input and output format as the public dataset, but it does not include a public answer key. The local evaluator can check whether a submission runs and emits valid JSON, but it cannot calculate semantic accuracy for validation data.

The hidden benchmark and hidden labels are not distributed in this repository.

## Evaluation Workflow

A participant submission provides a `run.py` program. The evaluator calls it once per instance:

```bash
python run.py <instance_directory>
```

The program must print exactly one JSON object to stdout:

```json
{"instance_id": "...", "decision": "EQUIVALENT"}
```

or:

```json
{"instance_id": "...", "decision": "NON_EQUIVALENT"}
```

Optional `evidence` and `counterexample` fields may be included as JSON objects for diagnostics.

For public data, the local evaluator compares decisions to the included public labels. For validation data, the local evaluator reports valid outputs as `VALID_UNSCORED` because labels are not public.

## Successful Solutions

A successful solution produces valid JSON for each instance and makes accurate semantic equivalence decisions under the declared mode. Runtime and resource use matter after correctness, especially for official-style evaluation where timeout and isolation policies may be enforced.

High accuracy is not itself considered a problem. The intended goal is to solve the stated equivalence task, not to defeat a formatting trick.

## Known Limitations

V1 focuses on unitary circuit equivalence for the supported OpenQASM subset described in `SPECIFICATION.md`. Measurements, resets, classical control, noise models, pulse schedules, hardware topology, calibration data, cloud quantum hardware behavior, and proprietary runtime behavior are out of scope.

Symbolic all-real parameter equivalence is not part of the V1 scored core. Public local validation does not reveal validation or hidden labels.

## Intended Use

The package is intended for research prototyping, educational exercises, solver development, and reproducible discussion of quantum circuit equivalence workflows. It should not be described as a peer-reviewed benchmark paper.

## Citation

If you use this challenge or its datasets in research, cite this repository using `CITATION.cff`:

```text
Quantum Circuit Equivalence Challenge. Quark Quantum.
https://github.com/Quark-Quantum/quantum-circuit-equivalence-challenge
```

A future benchmark paper may provide a preferred scholarly citation.
