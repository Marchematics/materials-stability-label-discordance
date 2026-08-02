from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "evidence_strengthening_v1"
V3 = ROOT / "outputs" / "referee_revision_v3"

def test_training_overlap_audit_tracks_all_real_models() -> None:
    x = pd.read_csv(OUT / "model_training_overlap" / "model_training_overlap_audit.csv")
    assert set(x.model) == {"ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP"}
    assert set(x.M1_row_n) == {31_872}

def test_source_input_card_has_three_declared_sources() -> None:
    x = pd.read_csv(V3 / "source_input_card" / "source_input_card.csv")
    assert set(x.source) == {"Materials Project", "MatterGen alex-mp-20", "official Alexandria-PBE"}
    assert x.native_hull_input.notna().all() and x.analysis_hull_field.notna().all()

def test_mphys_support_audit_matches_revision_cohort() -> None:
    x = pd.read_csv(V3 / "mphys_support_exclusion_audit" / "mphys_retained_excluded_summary.csv")
    retained = x.loc[x.group.eq("Mphys retained"), "n_group"].iloc[0]
    excluded = x.loc[x.group.eq("candidate excluded"), "n_group"].iloc[0]
    assert int(retained) == 36_650
    assert int(excluded) == 31

def test_revision_manifest_records_current_estimand() -> None:
    d = json.loads((V3 / "manifest_referee_revision_v3.json").read_text())
    assert d["estimand"].startswith("leave-one-tolerance-equivalence-class-out")
    assert d["evaluation_summary"]["mphys_n"] == 36_650
