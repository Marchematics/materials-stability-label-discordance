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

    local = status[status["component"].eq("ALIGNN-FF local explicit-path scorer")].iloc[0]
    assert local["status"] == "partial_pass_public_source_pending"
    assert "smoke tests" in local["details"]


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
    remote = downloads[downloads["url_pattern"].ne("local_user_provided_archive")]
    assert set(remote["status_code"].astype(str)) == {"403"}
    assert set(remote["zip_ok"].astype(str).str.lower()) == {"false"}
    assert set(remote["decision"]) == {"blocked_not_model_zip"}
    local = downloads[downloads["url_pattern"].eq("local_user_provided_archive")].iloc[0]
    assert str(local["zip_ok"]).lower() == "true"
    assert local["sha256"] == "ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5"

    smoke = pd.read_csv(MILESTONE / "table_alignn_ff_smoke_tests.csv")
    zip_row = smoke[smoke["smoke_test"].eq("zip_integrity")].iloc[0]
    assert zip_row["status"] == "fail"
    si = smoke[smoke["smoke_test"].eq("si_unrelaxed_energy_cpu")].iloc[0]
    assert si["status"] == "pass"
    matched = smoke[smoke["smoke_test"].eq("matched_structure_single_cpu")].iloc[0]
    assert matched["status"] == "pass"
    blocked = smoke[smoke["status"].eq("blocked")]
    assert len(blocked) >= 3

    repair = (MILESTONE / "ALIGNN_FF_PINNED_DOWNLOADER_REPAIR.md").read_text(
        encoding="utf-8"
    )
    assert "issue #194" in repair
    assert "local technical scorer smoke gate" in repair


def test_route_c_is_separate_protocol_not_route_b_modification() -> None:
    protocol = (MILESTONE / "ROUTE_C_ALTERNATIVE_FRONTIER_PANEL_PROTOCOL.md").read_text(
        encoding="utf-8"
    )
    assert "Route B remains unconsumed and blocked" in protocol
    assert "Route C is not a continuation of Route B" in protocol
    assert "CHGNet" in protocol
    assert "MACE-MP" in protocol
    assert "SevenNet / MatterSim / Orb / MatGL / M3GNet" in protocol
    assert "stable-class F1" in protocol

    panel = pd.read_csv(MILESTONE / "table_route_c_frontier_panel_protocol.csv")
    assert {"CHGNet", "MACE-MP"}.issubset(set(panel["model"]))
    alignn = panel[panel["model"].eq("ALIGNN-FF")].iloc[0]
    assert alignn["route_c_role"] == "excluded_from_route_c_due_to_readiness_block"

    gates = pd.read_csv(MILESTONE / "table_route_c_go_no_go_gate.csv")
    independence = gates[gates["gate"].eq("route_c_independence")].iloc[0]
    assert independence["current_status"] == "pass_protocol_frozen"
    ranking = gates[gates["gate"].eq("ranking_flip_gate")].iloc[0]
    assert "abs F1 delta >= 0.05" in ranking["requirement"]


def test_route_c_existing_probe_completed_but_not_full_primary() -> None:
    scores = pd.read_csv(MILESTONE / "table_route_c_existing_probe_model_scores.csv")
    assert {"CHGNet", "MACE-MP", "M3GNet"}.issubset(set(scores["model"]))
    assert scores.groupby("model")["material_id"].nunique().min() == 270

    metrics = pd.read_csv(MILESTONE / "table_route_c_existing_probe_ranking_metrics.csv")
    assert set(metrics["label_source"]) == {"WBM", "alex-mp"}
    assert metrics["n_common"].min() == 270

    summary = pd.read_csv(MILESTONE / "table_route_c_existing_probe_flip_summary.csv").iloc[0]
    assert summary["status"] == "run_existing_probe_not_full_mp_alex_route_c"
    assert str(summary["top_model_flip"]).lower() == "false"
    assert str(summary["ordering_flip"]).lower() == "false"
    assert summary["go_no_go"] == "NO_GO_existing_probe_no_material_F1_ranking_flip"
    assert "not full MP-vs-Alex Route C primary" in summary["claim_scope"]


def test_route_b_alignn_ff_provenance_blocks_primary_claim_until_public_source() -> None:
    checklist = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_provenance_checklist.csv")
    archive = checklist[checklist["check_item"].eq("archive_sha256")].iloc[0]
    assert archive["value"] == "ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5"
    tech = checklist[checklist["check_item"].eq("si_smoke")].iloc[0]
    assert tech["status"] == "pass"

    decision = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_eligibility_decision.csv")
    registry = decision[decision["gate"].eq("public_registry_gate")].iloc[0]
    assert registry["status"] == "pass"
    clean = decision[decision["gate"].eq("clean_download_hash_match")].iloc[0]
    assert clean["status"] == "pending_blocked_403"
    primary = decision[decision["gate"].eq("route_b_primary_evidence_gate")].iloc[0]
    assert primary["status"] == "pending_hash_match"
    assert "do not run one-shot Route B primary claim yet" in primary["decision"]

    note = (MILESTONE / "ROUTE_B_ALIGNN_FF_PROVENANCE_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "public registry entry exists" in note
    assert "PENDING_HASH_MATCH" in note


def test_route_b_public_provenance_unlock_requires_clean_hash_match() -> None:
    unlock = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_public_provenance_unlock.csv")
    registry = unlock[unlock["gate"].eq("public_registry")].iloc[0]
    assert registry["status"] == "pass"
    clean = unlock[unlock["gate"].eq("clean_download_hash_match")].iloc[0]
    assert clean["status"] == "pending_blocked_403"
    primary = unlock[unlock["gate"].eq("route_b_primary_evidence_gate")].iloc[0]
    assert primary["status"] == "pending_hash_match"

    text = (MILESTONE / "ROUTE_B_ALIGNN_FF_PUBLIC_PROVENANCE_UNLOCK.md").read_text(
        encoding="utf-8"
    )
    assert "public registry gate: PASS" in text
    assert "clean download hash match: PENDING" in text
    assert "Route B one-shot outcome: unconsumed" in text


def test_route_b_runner_records_data_access_gate_without_credentials() -> None:
    runner = ROOT / "scripts" / "run_route_b_full_snapshot_rescue.py"
    assert runner.exists()
    text = runner.read_text(encoding="utf-8")
    assert "MP_API_KEY environment variable is required" in text
    assert "credentials are not read from files" in text

    failure = pd.read_csv(MILESTONE / "table_route_b_full_snapshot_data_access_failure.csv")
    row = failure.iloc[0]
    assert row["stage"] == "mp_api_fetch"
    assert str(row["status"]).startswith("failed")
    assert row["error_type"] == "RuntimeError"

    closeout = (MILESTONE / "ROUTE_B_FULL_SNAPSHOT_RESCUE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert (
        "blocked at MP API data-access gate" in closeout
        or "Status: completed diagnostic" in closeout
    )


def test_route_b_full_snapshot_diagnostic_keeps_nmi_line_closed() -> None:
    summary = pd.read_csv(MILESTONE / "table_route_b_full_snapshot_summary.csv").iloc[0]
    assert int(summary["n_common"]) >= 200
    assert float(summary["discordance_rate"]) < 0.40
    assert str(summary["top_model_flip"]).lower() == "false"
    assert str(summary["ordering_flip"]).lower() == "false"
    assert summary["go_no_go"] == "NO_GO_keep_NMI_line_closed"


def test_selection_conditional_discordance_no_go() -> None:
    top = pd.read_csv(MILESTONE / "table_selection_conditional_top_decile_summary.csv")
    assert set(top["model"]) == {"ALIGNN-FF", "CHGNet", "MACE-MP"}
    assert top["top_decile_discordance"].max() < 0.30
    assert top["top_decile_enrichment"].max() < 2.0

    go = pd.read_csv(MILESTONE / "table_selection_conditional_go_no_go.csv").iloc[0]
    assert go["launch_gate"] == "NO_GO"
    assert int(go["n_models_passing"]) == 0


def test_manifest_exists() -> None:
    assert (MILESTONE / "MANIFEST_SHA256.txt").exists()
    assert (ROOT / "MANIFEST_SHA256.txt").exists()
