#!/usr/bin/env python3
"""Generate and verify the DD manuscript claim ledger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sourceaware.dd_submission import DEFAULT_OUT, DEFAULT_PHASE1, DEFAULT_PHASE2, write_claims_outputs


FORBIDDEN_UNQUALIFIED = [
    r"homogeneous DFT (?:truth|referee) labels (?:show|demonstrate|confirm)",
    r"generated materials (?:are|were) validated",
]


def audit_text(path: Path, claims: dict[str, object]) -> list[str]:
    if not path.exists():
        return [f"manuscript not found: {path}"]
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    # Terminology: D0 is retained only inside frozen input filenames, never as
    # the public manuscript set name.
    if re.search(r"\bD0\b", text):
        problems.append("manuscript still uses D0; use F0 formula-support catalogue")
    required = [
        "F0 is a formula-support catalogue",
        "ALIGNN-FF",
        "CHGNet",
        "M3GNet",
        "MACE-MP",
        "diagnostic rankings",
        "not calibrated source-comparable hull distances",
        "not physical truth",
        "does not provide homogeneous DFT referee",
        "does not validate generated materials",
    ]
    for phrase in required:
        if phrase.lower() not in text.lower():
            problems.append(f"required evidence-boundary phrase missing: {phrase}")
    for pattern in FORBIDDEN_UNQUALIFIED:
        if re.search(pattern, text, flags=re.IGNORECASE):
            problems.append(f"forbidden unqualified claim matches: {pattern}")
    # Main narrative should not contain internal project-management terms.
    body = text.split("\\section*{Data availability}", 1)[0]
    project_patterns = {
        "Phase 1/2": r"\bPhase\s*~?\s*[12](?:\s*/\s*2)?\b",
        "branch": r"\bbranch\b",
        "workspace clean": r"\bworkspace\s+clean\b",
        "tests passed": r"\btests?\s+passed\b",
        "git diff": r"\bgit\s+diff\b",
    }
    for token, pattern in project_patterns.items():
        if re.search(pattern, body, flags=re.IGNORECASE):
            problems.append(f"internal project-management term in scientific narrative: {token}")
    # Section order required by DD lock.
    order = [
        "\\section*{Author contributions}",
        "\\section*{Conflicts of interest}",
        "\\section*{Data availability}",
        "\\section*{Acknowledgements}",
        "\\bibliography{references}",
    ]
    positions = [text.find(marker) for marker in order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        problems.append("final section order is not Author contributions, Conflicts, Data availability, Acknowledgements, References")
    if "\\section*{Code availability}" in text:
        problems.append("Code availability must be merged into Data availability")
    if "\\section*{Funding}" in text or "\\section*{Declaration of generative AI" in text:
        problems.append("Funding and AI-use disclosure must be merged into Acknowledgements")
    if "\\section{Conclusions}" not in text:
        problems.append("concise Conclusions section missing")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1", type=Path, default=DEFAULT_PHASE1)
    parser.add_argument("--phase2", type=Path, default=DEFAULT_PHASE2)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manuscript", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    claims = write_claims_outputs(args.out, args.phase1, args.phase2)
    issues: list[str] = []
    if args.manuscript:
        issues = audit_text(args.manuscript, claims)
    status = {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "manuscript": str(args.manuscript) if args.manuscript else None,
        "evidence_scope": claims["evidence_scope"],
    }
    (args.out / "manuscript_claims_check.json").write_text(json.dumps(status, indent=2) + "\n")
    if args.check and issues:
        raise SystemExit("Manuscript claims audit failed:\n- " + "\n- ".join(issues))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
