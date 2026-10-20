# Codex Instructions: AI Quality Gate Pilot

Scope: This is an **isolated test repository**, not a completed ChatGPT/Work/Codex-wide quality guarantee.

## Priorities
1. Preserve the user's original exact wording and requirements. Do not silently "correct" terms.
2. Distinguish requested outcome, tested behaviors, and real-world achieved outcome.
3. Never report a step as completed without evidence: command, exit code, or directly verifiable record.
4. When asked "Are you sure?", reassess independently. Only change the conclusion when specific new evidence or a clearly identified original error justifies it; compare before/after and evidence.
5. Preserve existing project files and constraints. Do not silently weaken tests or change baselines to make them pass.
6. For claims about current facts, use independent authoritative sources and cite them when available. A passing unit test does not prove external facts.
7. Keep status categories distinct: PASS for actually verified limited criteria, FAIL for demonstrated violation, PENDING for unverified.
8. Report observed outputs, limitations, missing requirements, unexpected outcomes, and failed tests. Do not conceal failures.

## Required commands before completion claims
- `python -m unittest discover -s tests -v`
- `python quality_gate.py --root . --report quality_gate_report.json`
- Review `quality_gate_report.json` and actual GitHub Actions run when available.

These commands currently verify only this pilot's sample requirement R1. They **do not** verify the original overarching goal of automatic fact-checking for all ChatGPT, Work and Codex answers.

## CI safety
- Never put secrets in PR jobs; treat code and test commands from PRs as untrusted.
- Do not merge pilot changes into main or change branch protection.
- Any modification of the validation logic, baseline, workflow, or tests requires explicit disclosure and review.
