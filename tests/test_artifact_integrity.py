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


def test_manifest_exists() -> None:
    assert (MILESTONE / "MANIFEST_SHA256.txt").exists()
    assert (ROOT / "MANIFEST_SHA256.txt").exists()
