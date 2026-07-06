from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_phase1_label_views_present_and_consistent():
    labels=pd.read_parquet(OUT/'labels_by_view.parquet')
    required={'mp_native','alexmp20_native','alex_pbe_native','mp_common_pool','alex_pbe_common_pool','common_pool','mp_full_source_union','alex_pbe_full_source_union','source_union','all_source_native','consensus','consensus_stable','uncertain','audit_view'}
    assert required.issubset(set(labels.label_view))
    native=labels[labels.label_view.eq('mp_native')].copy().sort_values('row_id')
    row_ids=native.row_id.tolist()
    assert native.label.notna().all()
    unc=labels[labels.label_view.eq('uncertain')].set_index('row_id').loc[row_ids]
    consensus_state=native.set_index('row_id').loc[row_ids, 'consensus_label']
    expected=~consensus_state.isin(['consensus_stable','consensus_unstable'])
    assert (unc.label.astype(bool).to_numpy()==expected.to_numpy()).all()
    cp=labels[labels.label_view.eq('common_pool')].set_index('row_id').loc[row_ids]
    cp_mp=labels[labels.label_view.eq('mp_common_pool')].set_index('row_id').loc[row_ids].label.astype('boolean')
    cp_ax=labels[labels.label_view.eq('alex_pbe_common_pool')].set_index('row_id').loc[row_ids].label.astype('boolean')
    cp_agree=cp_mp.notna() & cp_ax.notna() & (cp_mp==cp_ax)
    assert cp.is_evaluable.to_numpy().sum()==int(cp_agree.sum())
    consensus=labels[labels.label_view.eq('consensus')].set_index('row_id').loc[row_ids]
    assert (consensus.label.astype('boolean').fillna(False).to_numpy()==consensus_state.eq('consensus_stable').to_numpy()).all()
    su=labels[labels.label_view.eq('source_union')]
    assert su.label.isna().all()
    assert not su.is_evaluable.any()
