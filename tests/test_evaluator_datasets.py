from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "evaluator") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluator"))

try:
    from evaluator.evaluate import evaluate, parse_stdout  # noqa: E402
except ImportError:
    from evaluate import evaluate, parse_stdout  # type: ignore # noqa: E402


class EvaluatorDatasetTests(unittest.TestCase):
    def test_public_dataset_scores_with_public_answer_key(self) -> None:
        report = evaluate(ROOT / "starter", ROOT / "public_dataset", timeout=5.0)

        summary = report["summary"]
        self.assertEqual(report["dataset"], "official_public_v1")
        self.assertIs(summary["scoring_available"], True)
        self.assertEqual(summary["instance_count"], 6)
        self.assertEqual(summary["valid_outputs"], 6)
        self.assertEqual(summary["invalid_outputs"], 0)
        self.assertEqual(summary["correct"], 3)
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual({row["status"] for row in report["instances"]}, {"CORRECT", "INCORRECT"})

    def test_validation_dataset_accepts_protocol_without_public_answer_key(self) -> None:
        report = evaluate(ROOT / "starter", ROOT / "validation_dataset", timeout=5.0)

        summary = report["summary"]
        self.assertEqual(report["dataset"], "official_validation_v1")
        self.assertIs(summary["scoring_available"], False)
        self.assertEqual(summary["instance_count"], 12)
        self.assertEqual(summary["valid_outputs"], 12)
        self.assertEqual(summary["invalid_outputs"], 0)
        self.assertEqual(summary["correct"], 0)
        self.assertIsNone(summary["accuracy"])
        self.assertIn("does not include a public answer key", summary["message"])
        self.assertEqual({row["status"] for row in report["instances"]}, {"VALID_UNSCORED"})
        self.assertTrue(all(row["truth"] is None for row in report["instances"]))
        self.assertTrue(all(row["correct"] is None for row in report["instances"]))

    def test_public_and_validation_use_same_participant_output_schema(self) -> None:
        minimal_public, public_errors = parse_stdout(
            b'{"instance_id":"dev_exact_equiv_001","decision":"EQUIVALENT"}',
            "dev_exact_equiv_001",
        )
        minimal_validation, validation_errors = parse_stdout(
            b'{"instance_id":"val_00000","decision":"NON_EQUIVALENT"}',
            "val_00000",
        )

        self.assertEqual(public_errors, [])
        self.assertEqual(validation_errors, [])
        self.assertEqual(set(minimal_public), {"instance_id", "decision"})
        self.assertEqual(set(minimal_validation), {"instance_id", "decision"})

    def test_valid_equivalent_and_non_equivalent_decisions_are_accepted(self) -> None:
        equivalent, equivalent_errors = parse_stdout(
            b'{"instance_id":"case_a","decision":"EQUIVALENT"}',
            "case_a",
        )
        non_equivalent, non_equivalent_errors = parse_stdout(
            b'{"instance_id":"case_b","decision":"NON_EQUIVALENT"}',
            "case_b",
        )

        self.assertEqual(equivalent_errors, [])
        self.assertEqual(non_equivalent_errors, [])
        self.assertEqual(equivalent["decision"], "EQUIVALENT")
        self.assertEqual(non_equivalent["decision"], "NON_EQUIVALENT")

    def test_malformed_output_is_rejected(self) -> None:
        parsed, errors = parse_stdout(b"not-json", "case_a")

        self.assertEqual(parsed, {})
        self.assertTrue(any("stdout is not valid JSON" in error for error in errors))

    def test_invalid_decision_is_rejected(self) -> None:
        parsed, errors = parse_stdout(
            b'{"instance_id":"case_a","decision":"UNSUPPORTED"}',
            "case_a",
        )

        self.assertEqual(parsed["decision"], "UNSUPPORTED")
        self.assertIn("decision must be EQUIVALENT or NON_EQUIVALENT", errors)

    def test_unknown_instance_id_is_rejected(self) -> None:
        parsed, errors = parse_stdout(
            b'{"instance_id":"wrong_case","decision":"EQUIVALENT"}',
            "case_a",
        )

        self.assertEqual(parsed["instance_id"], "wrong_case")
        self.assertIn("wrong instance_id", errors)

    def test_missing_public_answer_key_never_raises_key_error(self) -> None:
        try:
            report = evaluate(ROOT / "starter", ROOT / "validation_dataset", timeout=5.0)
        except KeyError as exc:
            self.fail(f"missing public_answer_key raised KeyError: {exc}")

        self.assertFalse(report["summary"]["scoring_available"])
        self.assertIsNone(report["summary"]["accuracy"])

    def test_non_object_json_is_rejected(self) -> None:
        parsed, errors = parse_stdout(b'["not", "an", "object"]', "case_a")

        self.assertEqual(parsed, {})
        self.assertEqual(errors, ["stdout JSON must be an object"])

    def test_missing_required_fields_are_rejected(self) -> None:
        missing_instance, instance_errors = parse_stdout(
            b'{"decision":"EQUIVALENT"}',
            "case_a",
        )
        missing_decision, decision_errors = parse_stdout(
            b'{"instance_id":"case_a"}',
            "case_a",
        )

        self.assertNotIn("instance_id", missing_instance)
        self.assertIn("wrong instance_id", instance_errors)
        self.assertNotIn("decision", missing_decision)
        self.assertIn("decision must be EQUIVALENT or NON_EQUIVALENT", decision_errors)

    def test_optional_diagnostic_fields_must_be_objects(self) -> None:
        parsed, errors = parse_stdout(
            b'{"instance_id":"case_a","decision":"EQUIVALENT","evidence":[],"counterexample":"none"}',
            "case_a",
        )

        self.assertEqual(parsed["decision"], "EQUIVALENT")
        self.assertIn("evidence must be an object", errors)
        self.assertIn("counterexample must be an object", errors)

    def test_multiple_json_objects_are_malformed_output(self) -> None:
        parsed, errors = parse_stdout(
            b'{"instance_id":"case_a","decision":"EQUIVALENT"}\n{"instance_id":"case_a","decision":"NON_EQUIVALENT"}',
            "case_a",
        )

        self.assertEqual(parsed, {})
        self.assertTrue(any("stdout is not valid JSON" in error for error in errors))

    def test_timeout_is_reported_without_semantic_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission = Path(tmp)
            (submission / "run.py").write_text(
                "import time\n"
                "time.sleep(2)\n",
                encoding="utf-8",
            )

            report = evaluate(submission, ROOT / "public_dataset", timeout=0.1)

        self.assertEqual({row["status"] for row in report["instances"]}, {"TIMEOUT"})
        self.assertTrue(all(row["decision"] is None for row in report["instances"]))
        self.assertEqual(report["summary"]["valid_outputs"], 0)

    def test_nonzero_exit_is_reported_as_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission = Path(tmp)
            (submission / "run.py").write_text(
                "import sys\n"
                "sys.exit(3)\n",
                encoding="utf-8",
            )

            report = evaluate(submission, ROOT / "public_dataset", timeout=5.0)

        self.assertEqual({row["status"] for row in report["instances"]}, {"CRASH"})
        self.assertTrue(all(row["decision"] is None for row in report["instances"]))
        self.assertEqual(report["summary"]["valid_outputs"], 0)


if __name__ == "__main__":
    unittest.main()
