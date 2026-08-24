# Quantum Circuit Equivalence Challenge

Black-Box Verification of Quantum Circuit Equivalence

Build a program that reads two OpenQASM circuits and decides whether they are equivalent under the semantic mode declared by the instance.

This is an open research challenge. You may use simulation, symbolic reasoning, canonicalization, randomized testing, SAT/SMT methods, hybrid approaches, or other lawful techniques.

## Quick Start

Use Python 3.10 or newer.

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python starter/run.py examples/simple_equivalent
.venv\Scripts\python evaluator/evaluate.py --submission starter --dataset public_dataset --out report.json
```

On macOS/Linux, replace `.venv\Scripts\python` with `.venv/bin/python`.

## What To Build

Create a submission program named `run.py` that accepts one argument: an instance directory containing `instance.json`, `circuit_a.qasm`, and `circuit_b.qasm`.

## Submission Format

Print exactly one JSON object to stdout:

```json
{"instance_id": "dev_exact_equiv_001", "decision": "EQUIVALENT"}
```

Allowed decisions are `EQUIVALENT` and `NON_EQUIVALENT`. Logs belong on stderr.

## Data

- `examples/` contains tiny examples for checking file I/O.
- `public_dataset/` contains public development instances and labels for local scoring.
- `validation_dataset/` contains unlabeled validation-style instances for protocol testing.

The hidden benchmark and answer key are not included.

## Local Evaluator

`evaluator/evaluate.py` is a protocol and public-development checker. It is not the official hidden evaluator and does not contain hidden answers.

## AI Usage

AI assistance is allowed. See `AI_USAGE.md` and `RULES.md`.

## More Detail

Read `CHALLENGE.md`, `SPECIFICATION.md`, `RULES.md`, and `SUBMISSION_GUIDE.md` before preparing a submission.
