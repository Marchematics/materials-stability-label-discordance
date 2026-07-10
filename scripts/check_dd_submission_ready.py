#!/usr/bin/env python3
"""Audit the local Digital Discovery submission bundle.

This checker is intentionally stricter than manuscript compilation.  It links
the frozen evidence release to the separately maintained manuscript directory
and writes a human-readable PASS/FAIL ledger.  It never interprets NMI or
homogeneous-referee scaffolds as scientific evidence for this submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Callable

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUSCRIPT = Path(
    "/root/source_native_benchmark_revision_2026-07-04/"
    "formal_rsc_digital_discovery_revision"
)
TAG = "v2.0.0-dd-submission"
ZENODO_PATTERN = re.compile(r"10\.5281/zenodo\.\d+", re.IGNORECASE)


def command(*args: str, cwd: Path = ROOT) -> tuple[int, str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_abstract_words(tex: str) -> int:
    # The RSC template places the abstract in the final \normalsize cell of the
    # title table rather than in an abstract environment.
    marker = "& \\noindent\\normalsize{"
    start = tex.find(marker)
    if start < 0:
        return 0
    start += len(marker)
    end = tex.find("} \\\\\n\\end{tabular}", start)
    if end < 0:
        return 0
    text = tex[start:end]
    text = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+|[{}$~]", " ", text)
    return len(re.findall(r"\b[\w'-]+\b", text))


def pdf_pages(path: Path) -> int:
    code, output = command("pdfinfo", str(path))
    if code:
        return 0
    match = re.search(r"^Pages:\s+(\d+)", output, re.MULTILINE)
    return int(match.group(1)) if match else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manuscript-dir", type=Path, default=DEFAULT_MANUSCRIPT)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manuscript = args.manuscript_dir.resolve()
    report = (args.report or manuscript / "DD_SUBMISSION_READY.md").resolve()
    claims_path = ROOT / "outputs/dd_submission_v2/manuscript_claims.json"
    manifest_path = ROOT / "outputs/dd_submission_v2/manifest_dd_submission_v2.json"
    main_tex = manuscript / "main.tex"
    bib_path = manuscript / "references.bib"
    si_tex = manuscript / "supplementary_information.tex"
    main_pdf = manuscript / "main.pdf"
    si_pdf = manuscript / "supplementary_information.pdf"
    docs = manuscript / "submission_documents"

    rows: list[tuple[str, bool, str]] = []

    def gate(name: str, condition: bool, detail: str) -> None:
        rows.append((name, bool(condition), detail))

    # 1. Numerical identities and evidence scope.
    claims = json.loads(claims_path.read_text()) if claims_path.exists() else {}
    identities = claims.get("conflict_identities", {})
    identity_ok = bool(identities) and all(bool(item) for item in identities.values())
    gate("Numerical decomposition identities", identity_ok, json.dumps(identities, sort_keys=True))
    gate(
        "Frozen DD evidence scope",
        claims.get("evidence_scope") == "frozen_phase1_v2_and_phase2_v1_only",
        str(claims.get("evidence_scope")),
    )

    # 2. Claim audit and terminology.
    audit_code, audit_out = command(
        "python",
        "scripts/audit_manuscript_claims.py",
        "--manuscript",
        str(main_tex),
        "--check",
    )
    gate("Manuscript claim/terminology audit", audit_code == 0, audit_out[-500:] or "PASS")

    tex = main_tex.read_text(encoding="utf-8") if main_tex.exists() else ""
    bib = bib_path.read_text(encoding="utf-8") if bib_path.exists() else ""
    abstract_words = extract_abstract_words(tex)
    gate("Abstract length", 190 <= abstract_words <= 220, f"{abstract_words} words (target 190--220)")

    section_markers = [
        r"\section*{Author contributions}",
        r"\section*{Conflicts of interest}",
        r"\section*{Data availability}",
        r"\section*{Acknowledgements}",
        r"\bibliography{references}",
    ]
    positions = [tex.find(marker) for marker in section_markers]
    gate(
        "Digital Discovery final-section order",
        all(position >= 0 for position in positions) and positions == sorted(positions),
        "Author contributions -> Conflicts -> Data availability -> Acknowledgements -> References",
    )
    reference_count = len(re.findall(r"^@\w+\{", bib, flags=re.MULTILINE))
    gate("Article-level bibliography", reference_count >= 50, f"{reference_count} BibTeX records")

    boundary_phrases = [
        "does not provide homogeneous DFT referee truth labels",
        "does not validate generated materials",
        "does not claim complete full-source-union hull reconstruction",
        "not physical truth",
        "Only four models with exact SourceAware row mapping enter the primary comparison",
        "not calibrated source-comparable hull distances",
    ]
    missing_boundary = [phrase for phrase in boundary_phrases if phrase.lower() not in tex.lower()]
    gate("Scientific evidence guardrails", not missing_boundary, "missing: " + "; ".join(missing_boundary) if missing_boundary else "PASS")
    narrative = tex.split(r"\section*{Data availability}", 1)[0]
    forbidden_scaffold = [token for token in ("NMI", "Phase 1", "Phase 2", "referee_core") if token.lower() in narrative.lower()]
    gate("No NMI/project scaffold in DD narrative", not forbidden_scaffold, ", ".join(forbidden_scaffold) or "PASS")

    # 3. Manuscript/SI compilation products.
    main_pages = pdf_pages(main_pdf) if main_pdf.exists() else 0
    si_pages = pdf_pages(si_pdf) if si_pdf.exists() else 0
    gate("Main manuscript PDF", main_pages > 0, f"{main_pages} pages; sha256={sha256(main_pdf)[:12] if main_pdf.exists() else 'missing'}")
    gate("Supplementary Information PDF", si_pages > 0, f"{si_pages} pages; sha256={sha256(si_pdf)[:12] if si_pdf.exists() else 'missing'}")
    log_text = "\n".join(
        path.read_text(errors="ignore")
        for path in (manuscript / "main.log", manuscript / "supplementary_information.log")
        if path.exists()
    )
    unresolved = re.findall(r"undefined references|undefined citations|LaTeX Error", log_text, re.IGNORECASE)
    gate("LaTeX reference/error audit", not unresolved, ", ".join(sorted(set(unresolved))) or "PASS")

    # 4. Figure and TOC package.
    fig_dir = ROOT / "outputs/dd_submission_v2/figures"
    figure_stems = [
        "fig1_sourceaware_discovery_curves",
        "fig2_near_threshold_discordance",
        "fig3_sourceaware_benchmark_layer",
        "fig4_model_rank_audit",
        "fig5_candidate_consequence",
    ]
    missing_figures = [
        f"{stem}.{suffix}"
        for stem in figure_stems
        for suffix in ("pdf", "tiff")
        if not (fig_dir / f"{stem}.{suffix}").exists()
    ]
    gate("Vector PDF and 600-dpi TIFF figures", not missing_figures, ", ".join(missing_figures) or "5 PDF/TIFF pairs")
    dpi_issues: list[str] = []
    for path in fig_dir.glob("*.tiff"):
        with Image.open(path) as image:
            dpi = image.info.get("dpi", (0, 0))
            if min(dpi) < 599:
                dpi_issues.append(f"{path.name}:{dpi}")
    gate("TIFF resolution", not dpi_issues, ", ".join(dpi_issues) or "all TIFF exports >=600 dpi")
    source_files = list((ROOT / "outputs/dd_submission_v2/figure_source_data").glob("fig*.csv"))
    gate("Figure source tables", len(source_files) >= 10, f"{len(source_files)} CSV tables")
    toc_text_path = docs / "toc_text.txt"
    toc_text = toc_text_path.read_text().strip() if toc_text_path.exists() else ""
    toc_tiff = docs / "toc_graphic.tiff"
    toc_size = (0, 0)
    if toc_tiff.exists():
        with Image.open(toc_tiff) as image:
            dpi = image.info.get("dpi", (600, 600))
            toc_size = (image.width / dpi[0] * 2.54, image.height / dpi[1] * 2.54)
    gate(
        "TOC graphic and text",
        len(toc_text) <= 250 and toc_size[0] <= 8.05 and toc_size[1] <= 4.05,
        f"{len(toc_text)} characters; {toc_size[0]:.2f} x {toc_size[1]:.2f} cm",
    )

    # 5. Reproducibility and manifest integrity.
    required_repro = [
        "LICENSE", "CITATION.cff", "environment.yml", "requirements-lock.txt",
        "Dockerfile", "REPRODUCIBILITY.md", "DATA_PROVENANCE.md", "run_all.sh",
    ]
    missing_repro = [name for name in required_repro if not (ROOT / name).exists()]
    gate("Reproducibility bundle", not missing_repro, ", ".join(missing_repro) or "PASS")
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    bad_hashes: list[str] = []
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if not path.exists() or sha256(path) != item["sha256"]:
            bad_hashes.append(item["path"])
    gate("DD manifest integrity", bool(manifest.get("files")) and not bad_hashes, ", ".join(bad_hashes[:5]) or f"{len(manifest.get('files', []))} files verified")
    pytest_log = ROOT / "outputs/dd_submission_v2/logs/pytest.log"
    clean_log = ROOT / "outputs/dd_submission_v2/logs/clean_environment_regeneration.log"
    run_status = ROOT / "outputs/dd_submission_v2/logs/run_all.status"
    pytest_text = pytest_log.read_text(errors="ignore") if pytest_log.exists() else ""
    clean_text = clean_log.read_text(errors="ignore") if clean_log.exists() else ""
    pytest_match = re.search(r"(\d+) passed", pytest_text)
    clean_match = re.search(r"(\d+) passed", clean_text)
    gate(
        "Frozen DD test suite",
        bool(pytest_match) and " failed" not in pytest_text.lower(),
        f"{pytest_match.group(1)} passed" if pytest_match else "missing successful pytest summary",
    )
    gate(
        "Clean-environment regeneration",
        bool(clean_match) and " failed" not in clean_text.lower(),
        f"{clean_match.group(1)} passed" if clean_match else "missing successful pytest summary",
    )
    gate("run_all acceptance command", run_status.exists() and run_status.read_text().strip() == "PASS", run_status.read_text().strip() if run_status.exists() else "missing")

    # 6. Submission documents and local RSC-format preflight.
    required_docs = [
        "cover_letter.pdf", "preferred_reviewers.csv", "reviewer_access_instructions.md",
        "final_submission_checklist.md", "toc_graphic.pdf", "toc_graphic.tiff", "toc_text.txt",
    ]
    missing_docs = [name for name in required_docs if not (docs / name).exists()]
    gate("Submission document package", not missing_docs, ", ".join(missing_docs) or "PASS")
    gate(
        "Local RSC submission preflight",
        (docs / "rsc_submission_preflight.md").exists()
        and "Overall status: PASS" in (docs / "rsc_submission_preflight.md").read_text(errors="ignore"),
        "official-guideline preflight record",
    )

    # 7. Immutable release and archive. These gates intentionally cannot be
    # bypassed with placeholders.
    head_code, head = command("git", "rev-parse", "HEAD")
    tag_code, tag_head = command("git", "rev-list", "-n", "1", TAG)
    gate("Immutable local release tag", head_code == 0 and tag_code == 0 and head == tag_head, f"HEAD={head[:12]}; tag={tag_head[:12] if tag_head else 'missing'}")
    remote_code, remote_tags = command("git", "ls-remote", "--tags", "origin", f"refs/tags/{TAG}")
    gate("Pushed release tag", remote_code == 0 and bool(remote_tags), remote_tags or "missing")
    gh_code, gh_out = command("gh", "release", "view", TAG, "--repo", "Marchematics/materials-stability-label-discordance", "--json", "url,isDraft,isPrerelease")
    gh_ok = gh_code == 0 and '"isDraft":false' in gh_out and '"isPrerelease":false' in gh_out
    gate("Published GitHub release", gh_ok, gh_out or "missing")

    doi_matches = sorted(set(ZENODO_PATTERN.findall(tex + "\n" + bib)))
    placeholders = re.findall(r"DOI to be inserted|\bTBD\b|\bTODO\b|PLACEHOLDER", tex + "\n" + bib, flags=re.IGNORECASE)
    gate("Zenodo DOI in manuscript", bool(doi_matches) and not placeholders, ", ".join(doi_matches) if doi_matches else "missing or placeholder")
    formal_citations = "SourceAware-Stability" in bib and bool(doi_matches)
    gate("Formal data/software citation", formal_citations, f"DOIs={', '.join(doi_matches) or 'none'}")

    passed = all(ok for _, ok, _ in rows)
    lines = [
        "# Digital Discovery submission readiness",
        "",
        f"**Overall status: {'PASS' if passed else 'FAIL'}**",
        "",
        "This ledger audits the submission against frozen Phase 1/2 evidence. It does not count NMI-upgrade or homogeneous-referee scaffolds as evidence.",
        "",
        "| Acceptance condition | Status | Evidence |",
        "|---|---:|---|",
    ]
    for name, ok, detail in rows:
        detail = detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    lines.extend([
        "",
        "## Evidence boundary",
        "",
        "No PASS in this report implies homogeneous DFT referee truth, generated-material validation or complete source-union reconstruction. Common-pool, source-union, consensus and audit views remain benchmark diagnostics.",
        "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"{'PASS' if passed else 'FAIL'}: {report}")
    if args.check and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
