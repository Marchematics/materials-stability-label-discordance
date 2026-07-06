from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_phase1_label_views_present_and_consistent():
    labels=pd.read_parquet(OUT/'labels_by_view.parquet')
    required={'mp_native','alexmp20_native','alex_pbe_native','mp_common_pool','alex_pbe_common_pool','common_pool','mp_full_source_union','alex_pbe_full_source_union','source_union','all_source_native','consensus','consensus_stable','uncertain','audit_view'}
    assert required.issubset(set(labels.label_view))
    ds=pd.read_parquet(ROOT/'outputs/SourceAware-Stability-36K/sourceaware_stability_36k.parquet')
    mp=labels[labels.label_view.eq('mp_native')].set_index('row_id').loc[ds.row_id]
    assert (mp.label.astype(bool).to_numpy()==ds.source_native_mp_label.astype(bool).to_numpy()).all()
    unc=labels[labels.label_view.eq('uncertain')].set_index('row_id').loc[ds.row_id]
    expected=~ds.consensus_label.isin(['consensus_stable','consensus_unstable'])
    assert (unc.label.astype(bool).to_numpy()==expected.to_numpy()).all()

    cp=labels[labels.label_view.eq('common_pool')].set_index('row_id').loc[ds.row_id]
    cp_agree=ds.common_pool_mp_label.astype('boolean').notna() & ds.common_pool_alexandria_label.astype('boolean').notna() & (ds.common_pool_mp_label.astype('boolean')==ds.common_pool_alexandria_label.astype('boolean'))
    assert cp.is_evaluable.to_numpy().sum()==int(cp_agree.sum())
    consensus=labels[labels.label_view.eq('consensus')].set_index('row_id').loc[ds.row_id]
    assert (consensus.label.astype('boolean').fillna(False).to_numpy()==ds.consensus_label.eq('consensus_stable').to_numpy()).all()
    su=labels[labels.label_view.eq('source_union')]
    assert su.label.isna().all()
    assert not su.is_evaluable.any()
