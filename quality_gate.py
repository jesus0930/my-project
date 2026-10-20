#!/usr/bin/env python3
"""Evidence-based quality gate pilot; does not fact-check AI answers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def assess(root: Path):
    policy_file = root / ".quality-gate/policy.json"
    hash_file = root / ".quality-gate/policy.sha256"
    claims_file = root / ".quality-gate/claims.json"
    expected = hash_file.read_text(encoding="utf-8").strip()
    if hashlib.sha256(policy_file.read_bytes()).hexdigest() != expected:
        return {"overall": "FAIL", "items": [], "errors": ["Policy baseline changed"]}
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    claims = json.loads(claims_file.read_text(encoding="utf-8"))
    if not isinstance(policy.get("original_request"), str) or not policy["original_request"].strip():
        raise ValueError("Original request required")
    requirements = policy.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("Nonempty requirements required")
    if not isinstance(claims.get("items"), list):
        raise ValueError("Claims items required")
    ids = [r["id"] for r in requirements]
    if len(set(ids)) != len(ids) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("Unique requirement IDs required")
    items = []
    reported = {x.get("id"): x for x in claims["items"] if isinstance(x, dict)}
    for req in requirements:
        rid = req["id"]
        claim = reported.get(rid)
        if claim is None or claim.get("status") not in {"done", "partial", "not_done", "unknown"}:
            items.append({"id": rid, "status": "FAIL", "reason": "Missing or invalid claim"})
            continue
        if claim["status"] != "done":
            items.append({"id": rid, "status": "PENDING", "reason": "Requirement not finished"})
            continue
        proof = req.get("proof", {})
        if proof.get("type") != "command":
            items.append({"id": rid, "status": "PENDING", "reason": "No executable proof"})
            continue
        argv = proof.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
            items.append({"id": rid, "status": "FAIL", "reason": "Invalid command"})
            continue
        try:
            run = subprocess.run(argv, cwd=root, timeout=120, shell=False, capture_output=True, text=True)
            items.append({"id": rid, "status": "PASS" if run.returncode == 0 else "FAIL",
                          "reason": "command exit=" + str(run.returncode)})
        except (OSError, subprocess.TimeoutExpired) as exc:
            items.append({"id": rid, "status": "FAIL", "reason": type(exc).__name__})
    if set(reported) != set(ids):
        items.append({"id": "SCOPE", "status": "PENDING", "reason": "Extra or omitted claims"})
    changes = claims.get("conclusion_changes", [])
    if not isinstance(changes, list):
        raise ValueError("Conclusion changes must be a list")
    for idx, change in enumerate(changes):
        if not isinstance(change, dict):
            raise ValueError("Invalid conclusion change")
        if change.get("before") != change.get("after"):
            items.append({"id": "CHANGE"+str(idx), "status": "PENDING" if change.get("new_evidence") else "FAIL",
                          "reason": "Conclusion change requires independent evidence review"})
    overall = "FAIL" if any(x["status"] == "FAIL" for x in items) else (
        "PENDING" if any(x["status"] == "PENDING" for x in items) else "PASS")
    if claims.get("overall_claim") == "completed" and overall != "PASS":
        items.append({"id": "COMPLETION", "status": "FAIL", "reason": "Unsupported completion claim"})
        overall = "FAIL"
    return {"overall": overall, "items": items, "errors": [],
            "limits": ["Passing commands cannot establish factual truth or real-world completion",
                       "Same-PR policy hashes are not independently approved"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path, default=Path("quality_gate_report.json"))
    args = parser.parse_args()
    try:
        result = assess(args.root.resolve())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"overall": "FAIL", "items": [], "errors": [str(exc)]}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
