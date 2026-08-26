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

or:

```json
{"instance_id": "dev_exact_nonequiv_001", "decision": "NON_EQUIVALENT"}
```

The same JSON schema is used for examples, public development data, validation data, and official-style evaluation. Required fields are `instance_id` and `decision`. Allowed decisions are exactly `EQUIVALENT` and `NON_EQUIVALENT`. Optional `evidence` and `counterexample` fields may be included as JSON objects. Logs belong on stderr.

## Data

- `examples/` contains tiny examples for checking file I/O.
- `public_dataset/` contains public development instances and public labels for local scoring.
- `validation_dataset/` contains unlabeled validation-style instances for protocol testing with the same participant output format.

The hidden benchmark and answer key are not included.

## Local Evaluator

`evaluator/evaluate.py` is a protocol and public-development checker. For `public_dataset`, it reports local correctness and accuracy using the public answer key. For `validation_dataset`, it checks that submissions run and emit valid JSON, but reports `accuracy: null` because no public validation answer key is included. It is not the official hidden evaluator and does not contain hidden answers.

## Benchmark

Researchers and educators may want the benchmark-oriented overview in `BENCHMARK.md`.

## Citation

If you use this challenge or its datasets in research, cite this repository using `CITATION.cff`. A future benchmark paper may provide a preferred scholarly citation.

## AI Usage

AI assistance is allowed. See `AI_USAGE.md` and `RULES.md`.

## More Detail

Read `CHALLENGE.md`, `SPECIFICATION.md`, `RULES.md`, and `SUBMISSION_GUIDE.md` before preparing a submission.
