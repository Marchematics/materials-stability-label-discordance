from pathlib import Path
import json, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_full_source_union_is_not_exact_match_union():
    su=pd.read_parquet(OUT/'source_union_hull_labels.parquet')
    status=json.loads((OUT/'source_union_hull_status.json').read_text())
    assert status['status']=='incomplete'
    assert status['full_source_union_labels_available'] is False
    assert su.full_source_union_mp_label.isna().all()
    assert su.baseline_compatibility_only.astype(bool).all()
    assert su.pool_scope.eq('full_source_union_required_but_not_constructed').all()
def test_conflict_decomposition_has_required_components():
    dec=pd.read_csv(OUT/'conflict_decomposition.csv')
    assert {'source_native','common_pool','source_union'} <= {('source_native' if scope.startswith('source_native') else ('common_pool' if 'common_pool' in scope else ('source_union' if 'source_union' in scope or scope=='full_source_union' else scope))) for scope in dec.scope}
    assert {'phase_pool_sensitive_component','source_union_sensitive_component','persistent_source_energy_workflow_component','unreconstructable_full_source_union_rows'}.issubset(set(dec.component))
    assert int(dec[dec.component.eq('unreconstructable_full_source_union_rows')].n.iloc[0])==36802
