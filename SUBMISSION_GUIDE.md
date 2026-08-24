# Submission Guide

Your submission should provide an executable `run.py` that accepts one argument: the path to an instance directory.

```bash
python run.py <instance_directory>
```

Example:

```bash
python starter/run.py examples/simple_equivalent
```

Expected JSON format:

```json
{
  "instance_id": "simple_equivalent",
  "decision": "EQUIVALENT"
}
```

## stdout

Print exactly one JSON object to stdout. Do not print logs, progress bars, or extra text to stdout.

## stderr

Diagnostic logs may be written to stderr.

## Exit Codes

Exit code `0` means the program completed and stdout should contain the JSON response. Nonzero exit codes are treated as crashes by local and official-style evaluators.

## Timeout

If a program exceeds the configured timeout, the evaluator records a timeout. Design submissions to terminate predictably.

## Invalid JSON

Malformed JSON, wrong `instance_id`, missing `decision`, or an unsupported `decision` value is invalid output.

## Unsupported Instances

The official decision field has only `EQUIVALENT` and `NON_EQUIVALENT`. If your solver cannot handle an instance, it should still emit one of those decisions or accept that the case may be scored incorrect. Do not emit `UNSUPPORTED` as the final decision.

## Optional Evidence

You may include an `evidence` object for diagnostics. It does not change the public evaluator score.

## Optional Counterexamples

You may include a `counterexample` object for diagnostics. It does not change the public evaluator score.

## Local Evaluator

```bash
python evaluator/evaluate.py --submission starter --dataset public_dataset --out report.json
```

The local evaluator checks protocol behavior and public development labels. It is not the official hidden evaluator.
