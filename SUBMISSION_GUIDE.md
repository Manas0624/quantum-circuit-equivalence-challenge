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

or:

```json
{
  "instance_id": "simple_non_equivalent",
  "decision": "NON_EQUIVALENT"
}
```

This is the only participant output schema for examples, `public_dataset`, `validation_dataset`, and official-style evaluation.

## stdout

Print exactly one JSON object to stdout. Do not print logs, progress bars, or extra text to stdout.

## stderr

Diagnostic logs may be written to stderr.

## Exit Codes

Exit code `0` means the program completed and stdout should contain the JSON response. Nonzero exit codes are treated as crashes by local and official-style evaluators.

## Timeout

The local evaluator runs `run.py` once per instance with `subprocess.run(..., timeout=...)`. The default local timeout is 5 seconds per instance and can be changed with `--timeout-seconds`. If a program exceeds the configured per-instance timeout, the evaluator records `TIMEOUT` for that instance and continues. A timeout is not converted into `EQUIVALENT` or `NON_EQUIVALENT`.

## Invalid Output

Malformed JSON, non-object JSON, wrong or missing `instance_id`, missing `decision`, an unsupported `decision` value, non-object `evidence`, or non-object `counterexample` is invalid output. Invalid output is reported as `INVALID_OUTPUT`.

The `instance_id` must exactly match the current instance's `instance.json`. An unknown or mismatched `instance_id` is invalid output. If no JSON object is printed for an instance, stdout parsing fails and the output is invalid.

The evaluator expects one JSON object per run. It does not accept batch arrays or multiple JSON objects on stdout. Duplicate JSON object keys are not a supported way to submit more than one record; emit each required field exactly once.

Datasets are expected to include every instance listed in `manifest.json`. If a supplied dataset is missing an instance directory or `instance.json`, that is a dataset/package integrity error. If your `run.py` cannot read a supplied instance and exits nonzero, the evaluator reports `CRASH` for that run.

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

The local evaluator checks protocol behavior and public development labels. For `public_dataset`, it uses the included `public_answer_key` to report `CORRECT`, `INCORRECT`, and accuracy.

You can also run:

```bash
python evaluator/evaluate.py --submission starter --dataset validation_dataset --out validation_report.json
```

The validation dataset uses the same submission JSON format but has no public answer key. The local evaluator checks whether each run produced valid output and reports `VALID_UNSCORED` with `accuracy: null`; it cannot calculate semantic accuracy for validation data or reveal hidden truth. It is not the official hidden evaluator.
