from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_model_complete_metrics_shape_and_bounds():
    d5=pd.read_parquet(OUT/'denominator_d5_model_complete.parquet')
    m=pd.read_csv(OUT/'model_metrics_by_label_view.csv')
    assert len(d5)==36801
    assert set(m.model)=={'ALIGNN-FF','CHGNet','MACE-MP','M3GNet'}
    assert m.model_complete_denominator_n.eq(36801).all()
    for c in ['auroc','auprc','f1']:
        vals=m[c].dropna(); assert ((0<=vals)&(vals<=1)).all()
    assert (OUT/'label_view_band_vs_model_spread.csv').exists()
    assert (OUT/'model_rank_inversions.csv').exists()
