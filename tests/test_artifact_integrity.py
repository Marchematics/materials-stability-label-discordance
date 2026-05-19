from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MILESTONE = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"


def test_no_secret_material_is_committed() -> None:
    texts = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and path.stat().st_size < 5_000_000:
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    combined = "\n".join(texts)
    credential_like = re.findall(
        r"(?i)(?:api[_-]?key|token|secret|credential)\s*[:=]\s*['\"]?([A-Za-z0-9_-]{16,})",
        combined,
    )
    assert credential_like == []


def test_minimal_discordance_probe_passes_launch_signal() -> None:
    probe = pd.read_csv(MILESTONE / "table_minimal_discordance_probe.csv")
    row = probe.iloc[0]
    assert int(row["matched_n"]) >= 200
    assert float(row["discordance_rate"]) >= 0.40
    assert str(row["launch_gate_discordance_ge_0_40"]).lower() == "true"


def test_primary_downstream_endpoint_is_not_overclaimed() -> None:
    summary = pd.read_csv(MILESTONE / "table_downstream_ranking_flip_summary.csv")
    primary = summary[summary["endpoint"].eq("primary_frontier_model_ranking")].iloc[0]
    assert primary["status"] == "run"
    assert primary["go_no_go"] == "NO_GO_primary_no_material_F1_ranking_flip"
    assert str(primary["top_model_flip"]).lower() == "false"


def test_route_b_is_one_shot_and_keeps_endpoint_frozen() -> None:
    text = (MILESTONE / "ROUTE_B_ONE_SHOT_RESCUE_PROTOCOL.md").read_text(encoding="utf-8")
    assert "Run this rescue at most once" in text
    assert "stable-class F1" in text
    assert "n_common >= 200" in text
    assert "discordance >= 0.40" in text
    assert "permanently close the NMI discordance" in text

    gate = pd.read_csv(MILESTONE / "table_route_b_rescue_gate.csv")
    assert "one_shot_only" in set(gate["gate"])
    assert "reopen_rule" in set(gate["gate"])
    reopen = gate[gate["gate"].eq("reopen_rule")].iloc[0]
    assert "discordance >= 0.40" in reopen["requirement"]
    assert "stable-F1 ranking flip" in reopen["requirement"]


def test_route_b_readiness_blocks_endpoint_without_alignn_ff() -> None:
    status = pd.read_csv(MILESTONE / "table_route_b_readiness_status.csv")
    alignn = status[status["component"].eq("ALIGNN-FF")].iloc[0]
    assert alignn["status"] == "fail"
    assert "BadZipFile" in alignn["details"]

    endpoint = status[status["component"].eq("Route B primary endpoint")].iloc[0]
    assert endpoint["status"] == "blocked"
    assert "ALIGNN" in endpoint["details"]


def test_alignn_ff_readiness_attempt_records_partial_wbm_predictions() -> None:
    attempts = pd.read_csv(MILESTONE / "table_alignn_ff_readiness_attempts.csv")

    official = attempts[attempts["attempt_type"].eq("official_scorer_download")]
    assert not official.empty
    assert set(official["status"]) == {"blocked_403"}

    pinned = attempts[attempts["attempt_type"].eq("pinned_downloader_repair")]
    assert not pinned.empty
    assert set(pinned["status"]) == {"blocked_403"}

    frozen = attempts[attempts["attempt_id"].eq("alignn_ff_wbm_predictions")].iloc[0]
    assert frozen["status"] == "available"
    assert frozen["sha256_or_response"] == (
        "dc75be97f3bce3ce724680065abf11a19bdc6a3928fdd77ccb42d3f62a02e593"
    )
    assert frozen["route_b_implication"] == (
        "can_support_WBM_intersection_diagnostics_but_does_not_score_full_MP_Alex_snapshot"
    )

    closeout = (MILESTONE / "ALIGNN_FF_READINESS_FIX_ATTEMPT.md").read_text(
        encoding="utf-8"
    )
    assert "not as a" in closeout and "complete fix" in closeout
    assert "No Route B endpoint" in closeout


def test_alignn_ff_pinned_downloader_repair_does_not_clear_gate() -> None:
    downloads = pd.read_csv(MILESTONE / "table_alignn_ff_download_integrity.csv")
    assert not downloads.empty
    assert set(downloads["status_code"]) == {403}
    assert set(downloads["zip_ok"].astype(str).str.lower()) == {"false"}
    assert set(downloads["decision"]) == {"blocked_not_model_zip"}

    smoke = pd.read_csv(MILESTONE / "table_alignn_ff_smoke_tests.csv")
    zip_row = smoke[smoke["smoke_test"].eq("zip_integrity")].iloc[0]
    assert zip_row["status"] == "fail"
    blocked = smoke[smoke["status"].eq("blocked")]
    assert len(blocked) >= 3

    repair = (MILESTONE / "ALIGNN_FF_PINNED_DOWNLOADER_REPAIR.md").read_text(
        encoding="utf-8"
    )
    assert "issue #194" in repair
    assert "does not clear the Route B gate" in repair


def test_manifest_exists() -> None:
    assert (MILESTONE / "MANIFEST_SHA256.txt").exists()
    assert (ROOT / "MANIFEST_SHA256.txt").exists()
