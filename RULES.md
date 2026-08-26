# Rules

This file describes technical challenge rules. It is not a legal agreement.

## Participation

Individual and team participation rules require published challenge approval before participation.

## Permitted Software

Participants may use custom code, open-source libraries, classical simulators, symbolic tools, and local models, subject to license and security obligations.

## AI/LLM/Agent Usage

AI assistance is allowed. Participants may use ChatGPT, Codex, Claude, Gemini, GitHub Copilot, autonomous coding agents, and local models unless later published challenge rules say otherwise.

## Internet and Network Policy During Evaluation

Official-style evaluation is expected to run with network access disabled. Submissions must not rely on external APIs, cloud quantum hardware, remote simulators, or unavailable local services.

## Prohibited Behavior

Do not tamper with benchmark files, attempt to access hidden data, hard-code private answers, read files outside permitted evaluation areas, exfiltrate data, or attack the evaluation infrastructure.

## Hidden Data

The hidden benchmark and hidden labels are not distributed publicly. Accessing or attempting to infer them through unauthorized channels is prohibited.

## Submission Limits

Exact submission limits and competition operations require published challenge approval before participation.

## Collaboration and Plagiarism

Collaboration and plagiarism policy requires published challenge/legal approval before publication. Participants remain responsible for code provenance and licenses.

## Evaluation Procedure

Submissions are run on instance directories and must emit the JSON protocol described in `SUBMISSION_GUIDE.md`. Accuracy is primary; runtime and memory are secondary after correctness.

The public development dataset includes labels for local scoring. The public validation dataset does not include labels and uses the same participant submission format; local validation checks protocol behavior without revealing correctness. Hidden or organizer-side evaluation may score against private labels that are not distributed in this repository.

Timeouts, crashes, malformed output, and invalid decisions are execution or protocol failures. They are not silently mapped to either semantic decision.
