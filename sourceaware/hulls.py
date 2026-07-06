from __future__ import annotations
from pathlib import Path
import pandas as pd
from .io import ROOT, PHASE1_OUT, ensure_dir, read_table, write_json, write_table
from .matching import stable_from_ehull, bool_series
DATASET=ROOT/'outputs/SourceAware-Stability-36K/sourceaware_stability_36k.parquet'
COMMON=ROOT/'outputs/milestones/common_pool_convex_hull_layer/table_common_pool_convex_hull_labels.csv'
EXACT=ROOT/'outputs/milestones/source_union_common_pool/source_union_common_pool_rows.csv'
def build_common_pool_hulls(out_dir=PHASE1_OUT):
    out_dir=ensure_dir(out_dir); ds=pd.read_parquet(DATASET); cp=read_table(COMMON)
    cp=cp.rename(columns={'material_id':'mp_id','official_alexandria_e_form':'official_alexandria_formation_energy_per_atom','mp_common_pool_e_above_hull':'mp_common_pool_ehull','official_alexandria_common_pool_e_above_hull':'alex_pbe_common_pool_ehull','mp_common_pool_stable':'mp_common_pool_label','official_alexandria_common_pool_stable':'alex_pbe_common_pool_label','common_pool_formula_count':'formula_phase_count','mechanism_component':'common_pool_mechanism_component'})
    cols=['mp_id','mp_e_above_hull','official_alexandria_e_above_hull','mp_formation_energy_per_atom','official_alexandria_formation_energy_per_atom','mp_stable_exact','official_alexandria_stable_exact','mp_common_pool_ehull','alex_pbe_common_pool_ehull','mp_common_pool_label','alex_pbe_common_pool_label','formula_phase_count','common_pool_mechanism_component']
    out=ds[['row_id','mp_id','official_alexandria_id','formula','chemical_system','structure_hash']].merge(cp[cols],on='mp_id',how='left',validate='one_to_one')
    out['pool_scope']='matched_denominator_common_pool'; out['pool_completeness_status']='complete_for_matched_pool_row'; out.loc[out.mp_common_pool_ehull.isna(),'pool_completeness_status']='mp_formation_energy_missing'
    out['failure_reason']=''; out.loc[out.mp_common_pool_ehull.isna(),'failure_reason']='mp_formation_energy_unavailable'
    out['mp_common_pool_label']=stable_from_ehull(out.mp_common_pool_ehull); out['alex_pbe_common_pool_label']=stable_from_ehull(out.alex_pbe_common_pool_ehull)
    write_table(out,out_dir/'common_pool_hull_labels.parquet'); return out
def build_source_union_hulls(out_dir=PHASE1_OUT):
    out_dir=ensure_dir(out_dir); ds=pd.read_parquet(DATASET); cp=pd.read_parquet(out_dir/'common_pool_hull_labels.parquet') if (out_dir/'common_pool_hull_labels.parquet').exists() else build_common_pool_hulls(out_dir)
    out=ds[['row_id','mp_id','official_alexandria_id','formula','chemical_system','structure_hash','source_native_mp_label','source_native_alexandria_label','source_native_mp_ehull','source_native_alexandria_ehull']].rename(columns={'source_native_alexandria_label':'source_native_alex_pbe_label','source_native_alexandria_ehull':'source_native_alex_pbe_ehull'})
    out=out.merge(cp[['row_id','mp_common_pool_label','alex_pbe_common_pool_label','mp_common_pool_ehull','alex_pbe_common_pool_ehull','formula_phase_count','common_pool_mechanism_component']],on='row_id',how='left')
    if EXACT.exists():
        ex=read_table(EXACT).rename(columns={'source_union_mp_ehull':'exact_match_source_union_mp_ehull','source_union_alexandria_ehull':'exact_match_source_union_alex_pbe_ehull','source_union_mp_label':'exact_match_source_union_mp_label','source_union_alexandria_label':'exact_match_source_union_alex_pbe_label','source_union_formula_count':'exact_match_source_union_formula_phase_count','source_union_pool_scope':'exact_match_source_union_pool_scope','hidden_conflict':'hidden_common_pool_source_union_conflict'})
        out=out.merge(ex[['row_id','exact_match_source_union_mp_ehull','exact_match_source_union_alex_pbe_ehull','exact_match_source_union_mp_label','exact_match_source_union_alex_pbe_label','exact_match_source_union_formula_phase_count','exact_match_source_union_pool_scope','matched_pool_resolved','source_union_pool_resolved','persistent_residual','hidden_common_pool_source_union_conflict']],on='row_id',how='left')
    for c in ['full_source_union_mp_ehull','full_source_union_alex_pbe_ehull','full_source_union_formula_phase_count']: out[c]=pd.NA
    out['full_source_union_mp_label']=pd.Series(pd.NA,index=out.index,dtype='boolean'); out['full_source_union_alex_pbe_label']=pd.Series(pd.NA,index=out.index,dtype='boolean')
    out['pool_scope']='full_source_union_required_but_not_constructed'; out['pool_completeness_status']='incomplete'; out['failure_reason']='mp_api_access_or_complete_full_phase_pool_not_available_in_public_artifact_build'
    out['phase_pool_sensitive_component']=out.common_pool_mechanism_component.astype(str).eq('phase_pool_component_removed_by_common_pool')
    out['source_union_sensitive_component']=pd.Series(pd.NA,index=out.index,dtype='boolean'); out['persistent_source_energy_workflow_component']=out.get('persistent_residual',False).fillna(False).astype(bool); out['hidden_common_pool_source_union_conflict']=out.get('hidden_common_pool_source_union_conflict',False).fillna(False).astype(bool); out['unreconstructable_row']=True; out['baseline_compatibility_only']=True
    write_table(out,out_dir/'source_union_hull_labels.parquet')
    native=out.source_native_mp_label.astype(bool)!=out.source_native_alex_pbe_label.astype(bool); common=(out.mp_common_pool_label.astype('boolean')!=out.alex_pbe_common_pool_label.astype('boolean')).fillna(False)
    dec=pd.DataFrame([['native_mp_alex_pbe_conflict',int(native.sum()),'source_native'],['matched_common_pool_conflict',int(common.sum()),'matched_common_pool'],['phase_pool_sensitive_component',int(out.phase_pool_sensitive_component.sum()),'matched_common_pool'],['source_union_sensitive_component',0,'full_source_union_incomplete'],['persistent_source_energy_workflow_component',int(out.persistent_source_energy_workflow_component.sum()),'exact_match_source_union_baseline'],['hidden_common_pool_source_union_conflicts',int(out.hidden_common_pool_source_union_conflict.sum()),'exact_match_source_union_baseline'],['unreconstructable_full_source_union_rows',len(out),'full_source_union']],columns=['component','n','scope']); dec['denominator_n']=len(out); dec['counts_sum_to_denominator']=False; write_table(dec,out_dir/'conflict_decomposition.csv')
    write_json({'diagnostic':'full_source_union_hull_reconstruction','status':'incomplete','full_source_union_labels_available':False,'exact_match_source_union_baseline_available':EXACT.exists(),'pool_scope':'full_source_union_required_but_not_constructed','failure_reason':out.failure_reason.iloc[0],'guardrail':'Exact-match source-union compatibility rows are retained only as a baseline diagnostic and are not relabeled as full-source-union hulls.'}, out_dir/'source_union_hull_status.json')
    return out
