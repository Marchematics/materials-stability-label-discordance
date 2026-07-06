from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_phase1_denominator_anchor_counts():
    assert len(pd.read_parquet(OUT/'denominator_d1_mp_alexmp20_exact.parquet'))==43139
    assert len(pd.read_parquet(OUT/'denominator_d2_triple_single_match.parquet'))==36802
    assert len(pd.read_parquet(OUT/'denominator_d5_model_complete.parquet'))==36801
