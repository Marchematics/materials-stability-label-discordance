from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_exact_denominators_not_formula_only_and_multiple_reported():
    d0=pd.read_parquet(OUT/'denominator_d0_formula.parquet'); d1=pd.read_parquet(OUT/'denominator_d1_mp_alexmp20_exact.parquet'); d2=pd.read_parquet(OUT/'denominator_d2_triple_single_match.parquet')
    assert d0.match_status.eq('formula_level_overlap_only').all()
    assert d1.structure_hash.nunique()==len(d1)
    assert len(d0)!=len(d1)
    assert 'multiple_match_status' in d2.columns
    assert d2.in_d2_triple_single_match.astype(bool).all()
