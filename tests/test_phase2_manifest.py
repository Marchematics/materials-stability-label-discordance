from pathlib import Path
import json, re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_manifest_and_leaderboard_cards():
    man = json.loads((OUT / "manifest_phase2_v1.json").read_text())
    assert man["phase"] == "phase2_v1"
    assert man["file_count"] >= 20
    for rec in man["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", rec["sha256"])
    lb = pd.read_csv(OUT / "leaderboard" / "sourceaware_leaderboard_alpha.csv")
    assert len(lb) >= 10
    card_dir = OUT / "leaderboard" / "leaderboard_model_cards"
    assert len(list(card_dir.glob("*.md"))) >= 10
    report = (OUT / "tests_report.md").read_text()
    assert "not homogeneous DFT validation" in report
