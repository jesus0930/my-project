#!/usr/bin/env python3
"""Conservative acceptance gate: status metadata is not independent evidence."""
import argparse
import json
import os
from pathlib import Path
import sys

REQUIRED = (
    "ORIGINAL_AND_FOLLOWUPS",
    "REAL_COMPLETION_PROOF",
    "UNSUPPORTED_CONCLUSION_REVERSALS",
    "REAL_CHROME_E2E",
    "CHAT_WORK_CODEX_COVERAGE",
    "INDEPENDENT_FACT_CHECK",
    "PRE_DELIVERY_GATING",
)
STATES = {"NOT_VERIFIED", "PARTIAL", "VERIFIED"}


def evaluate(status, external_approval=None):
    if not isinstance(status, dict) or not isinstance(status.get("goals"), dict):
        raise ValueError("goals must be an object")
    goals = status["goals"]
    if set(goals) != set(REQUIRED):
        raise ValueError("Goal set does not match the frozen required goal IDs")
    details = []
    for key in REQUIRED:
        item = goals[key]
        if not isinstance(item, dict) or item.get("state") not in STATES:
            raise ValueError("Invalid state for goal " + key)
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list) or not all(isinstance(v, str) and v.strip() for v in evidence):
            raise ValueError("Invalid evidence links for " + key)
        if item["state"] == "VERIFIED" and not evidence:
            raise ValueError("VERIFIED requires evidence for " + key)
        details.append({"goal": key, "state": item["state"], "evidence_count": len(evidence)})
    incomplete = [x["goal"] for x in details if x["state"] != "VERIFIED"]
    if incomplete:
        overall = "NOT_COMPLETED"
        reason = "One or more required goals lack completed verification"
    else:
        overall = "REVIEW_REQUIRED"
        reason = "Repository-controlled metadata cannot independently certify real-world completion"
    return {"overall": overall, "reason": reason, "goals": details, "unmet_goals": incomplete,
            "evidence_check": "STATUS_METADATA_ONLY",
            "limits": ["Passing local unit tests does not prove all AI answers are correct",
                       "A same-branch status file and evidence links are not independent approval",
                       "This pilot cannot observe the user's Windows Chrome or all ChatGPT Work Codex activity"]}


def render_markdown(result):
    rows = "\n".join("| " + x["goal"] + " | " + x["state"] + " | " + str(x["evidence_count"]) + " |" for x in result["goals"])
    return ("## Original goal acceptance: " + result["overall"] + "\n\n" + result["reason"] +
            "\n\n| Goal | State | Evidence count |\n|---|---|---:|\n" + rows +
            "\n\nPassing ordinary CI tests does not mean the original system is finished.\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", type=Path, default=Path("goal_acceptance.json"))
    parser.add_argument("--report", type=Path, default=Path("goal_acceptance_report.json"))
    args = parser.parse_args(argv)
    try:
        result = evaluate(json.loads(args.status.read_text(encoding="utf-8")))
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(render_markdown(result))
        print(render_markdown(result))
        return 1
    except (ValueError, OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        print("INVALID_OR_MISSING_EVIDENCE: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
