from pathlib import Path
import json, re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_manifest_and_leaderboard_cards():
    man = json.loads((OUT / "manifest_phase2_v1.json").read_text())
    assert man["phase"] == "phase2_v1"
    assert man["phase1_input"]["frozen_input"] is True
    assert re.fullmatch(r"[0-9a-f]{64}", man["phase1_input"]["manifest_sha256"])
    assert man["file_count"] >= 20
    for rec in man["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", rec["sha256"])
    lb = pd.read_csv(OUT / "leaderboard" / "sourceaware_leaderboard_alpha.csv")
    assert len(lb) >= 10
    assert {"best_label_view_stable_yield@1000", "worst_label_view_stable_yield@1000", "topK_stable_yield_band@1000"}.issubset(lb.columns)
    assert lb["best_label_view_stable_yield@1000"].notna().any()
    assert pd.to_numeric(lb["topK_stable_yield_band@1000"], errors="coerce").ge(0).all()
    card_dir = OUT / "leaderboard" / "leaderboard_model_cards"
    inv = pd.read_csv(OUT / "model_scores" / "model_score_inventory.csv")
    assert len(list(card_dir.glob("*.md"))) >= len(inv)
    for model in inv.model_name:
        safe = str(model).lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        assert (card_dir / f"{safe}.md").exists(), model
    chgnet_card = (card_dir / "chgnet.md").read_text()
    assert "Best label view stable_yield@1000" in chgnet_card
    assert "Worst label view stable_yield@1000" in chgnet_card
    assert "Top-K stable-yield band @1000" in chgnet_card
    report = (OUT / "tests_report.md").read_text()
    assert "not homogeneous DFT validation" in report


def test_phase2_acceptance_check_records_passes_and_guardrails():
    path = OUT / "phase2_acceptance_check.json"
    assert path.exists()
    checks = pd.read_json(path)
    required = {
        "phase1_frozen_input_present",
        "model_score_inventory",
        "model_denominators",
        "model_evaluation_label_views",
        "label_uncertainty_vs_model_spread",
        "rank_inversion_analysis",
        "generative_candidate_consequence",
        "leaderboard_alpha",
        "figures_and_source_data",
        "tests_and_reproducibility",
    }
    assert required == set(checks.check_id)
    assert not checks.status.eq("fail").any()
    gen = checks[checks.check_id.eq("generative_candidate_consequence")].iloc[0]
    assert gen.status == "guarded_partial"
    assert "no homogeneous DFT validation" in gen.guardrail
    assert (OUT / "phase2_acceptance_check.md").exists()
