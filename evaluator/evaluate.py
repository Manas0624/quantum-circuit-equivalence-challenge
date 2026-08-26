from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DECISIONS = {"EQUIVALENT", "NON_EQUIVALENT"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Protocol evaluator for public development data.")
    parser.add_argument("--submission", required=True, help="Directory containing run.py.")
    parser.add_argument("--dataset", required=True, help="Dataset directory containing manifest.json.")
    parser.add_argument("--out", required=True, help="Path for JSON report.")
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    args = parser.parse_args()
    report = evaluate(Path(args.submission), Path(args.dataset), args.timeout_seconds)
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"accuracy": report["summary"]["accuracy"], "valid": report["summary"]["valid_outputs"]}, sort_keys=True))
    return 0 if report["summary"]["invalid_outputs"] == 0 else 1


def evaluate(submission_dir: Path, dataset_dir: Path, timeout: float) -> dict[str, Any]:
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    answers: dict[str, str] = {}
    answer_key = manifest.get("public_answer_key")
    if answer_key is not None:
        answer_path = dataset_dir / answer_key
        for item in json.loads(answer_path.read_text(encoding="utf-8"))["answers"]:
            answers[item["instance_id"]] = item["decision"]
    scoring_available = bool(answers)
    rows = []
    for instance_id in manifest["instances"]:
        instance_dir = dataset_dir / "instances" / instance_id
        metadata = json.loads((instance_dir / "instance.json").read_text(encoding="utf-8"))
        start = time.perf_counter()
        try:
            completed = subprocess.run(
                [sys.executable, "run.py", str(instance_dir.resolve())],
                cwd=submission_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            runtime = time.perf_counter() - start
        except subprocess.TimeoutExpired:
            rows.append(_row(instance_id, None, answers.get(instance_id), "TIMEOUT", timeout, ["timeout"]))
            continue
        if completed.returncode != 0:
            rows.append(_row(instance_id, None, answers.get(instance_id), "CRASH", runtime, ["nonzero exit code"]))
            continue
        parsed, errors = parse_stdout(completed.stdout, metadata["instance_id"])
        if errors:
            rows.append(_row(instance_id, parsed.get("decision"), answers.get(instance_id), "INVALID_OUTPUT", runtime, errors))
            continue
        truth = answers.get(instance_id)
        if scoring_available:
            status = "CORRECT" if parsed["decision"] == truth else "INCORRECT"
        else:
            status = "VALID_UNSCORED"
        rows.append(_row(instance_id, parsed["decision"], truth, status, runtime, []))
    return {
        "report_type": "public_development",
        "dataset": manifest["dataset_id"],
        "summary": summarize(rows, scoring_available),
        "instances": rows,
    }


def parse_stdout(stdout: bytes, expected_instance_id: str) -> tuple[dict[str, Any], list[str]]:
    try:
        payload = json.loads(stdout.decode("utf-8").strip())
    except Exception as exc:  # noqa: BLE001
        return {}, [f"stdout is not valid JSON: {exc}"]
    errors = []
    if not isinstance(payload, dict):
        return {}, ["stdout JSON must be an object"]
    if payload.get("instance_id") != expected_instance_id:
        errors.append("wrong instance_id")
    if payload.get("decision") not in DECISIONS:
        errors.append("decision must be EQUIVALENT or NON_EQUIVALENT")
    if "evidence" in payload and not isinstance(payload["evidence"], dict):
        errors.append("evidence must be an object")
    if "counterexample" in payload and not isinstance(payload["counterexample"], dict):
        errors.append("counterexample must be an object")
    return payload, errors


def _row(instance_id: str, decision: str | None, truth: str | None, status: str, runtime: float, errors: list[str]) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "decision": decision,
        "truth": truth,
        "status": status,
        "correct": None if status == "VALID_UNSCORED" else status == "CORRECT",
        "runtime_seconds": runtime,
        "errors": errors,
    }


def summarize(rows: list[dict[str, Any]], scoring_available: bool) -> dict[str, Any]:
    valid = [r for r in rows if r["status"] in {"CORRECT", "INCORRECT", "VALID_UNSCORED"}]
    scored = [r for r in rows if r["status"] in {"CORRECT", "INCORRECT"}]
    summary: dict[str, Any] = {
        "instance_count": len(rows),
        "valid_outputs": len(valid),
        "invalid_outputs": len(rows) - len(valid),
        "correct": sum(1 for r in rows if r["status"] == "CORRECT"),
        "accuracy": sum(1 for r in rows if r["status"] == "CORRECT") / len(scored) if scored else None,
        "scoring_available": scoring_available,
        "total_runtime_seconds": sum(float(r["runtime_seconds"]) for r in rows),
    }
    if not scoring_available:
        summary["message"] = "Local scoring is unavailable because this dataset does not include a public answer key."
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
