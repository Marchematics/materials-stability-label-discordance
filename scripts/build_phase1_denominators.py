from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse, yaml
from pathlib import Path
import pandas as pd
from sourceaware.cards import write_source_cards
from sourceaware.io import ROOT, PHASE1_OUT, ensure_dir, sha256_file, write_json, write_manifest, write_table
from sourceaware.matching import denominator_base, row_hash
FULL=ROOT/'outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_structure_matches.csv'; TRIPLE=ROOT/'outputs/milestones/official_alexandria_pbe_extension/table_official_alexandria_single_match_triple_denominator.csv'; AUDIT=ROOT/'outputs/milestones/official_alexandria_pbe_feasibility/table_official_alexandria_pbe_denominator_row_audit.csv'; JARVIS=ROOT/'outputs/milestones/jarvis_multisource_extension/table_jarvis_default_exact_matches.csv'; DATASET=ROOT/'outputs/SourceAware-Stability-36K/sourceaware_stability_36k.parquet'; SCORES=ROOT/'outputs/milestones/model_leaderboard_impact/model_scores_public_safe.csv'; MODELS=['ALIGNN-FF','CHGNet','MACE-MP','M3GNet']
def source_map(ds,out):
    rows=[]
    for _,r in ds.iterrows():
        for source,field in [('mp','mp_id'),('alexmp20','mattergen_id'),('alex_pbe','official_alexandria_id')]: rows.append({'row_id':r.row_id,'source':source,'source_id':r.get(field,''),'has_source_id':bool(pd.notna(r.get(field,'')) and str(r.get(field,''))!='')})
    return write_table(pd.DataFrame(rows),out/'source_id_map.parquet')
def fingerprints(ds,out):
    d=ds[['row_id','mp_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); d['fingerprint_method']='public_safe_sha256_identifier_formula_site_proxy'; d['is_geometry_hash']=False; return write_table(d,out/'structure_fingerprints.parquet')
def sources_yaml(out):
    obj={'benchmark_layer':'SourceAware-Stability phase1_v2','sources':[{'source_id':'mp','name':'Materials Project','label_field':'source_native_mp_label','hull_field':'source_native_mp_ehull','unit':'eV/atom','formation_energy_available':True,'can_enter_common_pool_or_source_union_hull':True},{'source_id':'alexmp20','name':'MatterGen alex-mp-20','label_field':'source_native_mattergen_label','hull_field':'source_native_mattergen_ehull','unit':'eV/atom','formation_energy_available':False,'can_enter_common_pool_or_source_union_hull':False},{'source_id':'alex_pbe','name':'official Alexandria-PBE','label_field':'source_native_alexandria_label','hull_field':'source_native_alexandria_ehull','unit':'eV/atom','formation_energy_available':True,'can_enter_common_pool_or_source_union_hull':True},{'source_id':'jarvis','name':'JARVIS-DFT 3D','label_field':'jarvis_stable_exact','hull_field':'jarvis_ehull','unit':'eV/atom','formation_energy_available':False,'can_enter_common_pool_or_source_union_hull':False}], 'rules':{'stable_threshold':'e_above_hull <= 1e-8 eV/atom','label_scope':'benchmark diagnostics, not physical-truth labels'}}
    p=out/'data_sources.yaml'; p.write_text(yaml.safe_dump(obj,sort_keys=False),encoding='utf-8'); return p
def d0(full,triple,jarvis):
    parts=[]
    for name,df in [('mp_alexmp20',full),('triple',triple),('jarvis',jarvis)]:
        if len(df):
            tmp=df[['formula','chemical_system']].dropna().drop_duplicates(); tmp['source_subset']=name; parts.append(tmp)
    a=pd.concat(parts).groupby(['formula','chemical_system'])['source_subset'].agg(lambda x: sorted(set(x))).reset_index(); a['row_id']=[f'D0-{i:05d}' for i in range(1,len(a)+1)]; a['reduced_formula']=a.formula; a['structure_hash']=[row_hash('formula_only',f,c) for f,c in zip(a.formula,a.chemical_system)]; a['match_status']='formula_level_overlap_only'; a['duplicate_status']='not_structure_resolved'; a['multiple_match_status']='not_structure_resolved'; a['has_mp']=a.source_subset.map(lambda x:'mp_alexmp20'in x or 'triple'in x); a['has_alexmp20']=a.has_mp; a['has_alex_pbe']=a.source_subset.map(lambda x:'triple'in x); a['has_jarvis']=a.source_subset.map(lambda x:'jarvis'in x); a['source_subset']=a.source_subset.map(';'.join); a['in_d0_formula']=True; return denominator_base(a,'D0')
def d1(full):
    s=full[full.match_status.eq('strict_structure_match')].copy(); o=pd.DataFrame({'row_id':[f'D1-{i:05d}' for i in range(1,len(s)+1)],'mp_id':s.material_id.astype(str),'mattergen_id':'','formula':s.formula.astype(str),'reduced_formula':s.formula.astype(str),'chemical_system':s.chemical_system.astype(str),'structure_hash':[row_hash(r.material_id,r.formula,r.num_sites,r.mp_e_above_hull,r.alex_e_above_hull) for r in s.itertuples(index=False)],'match_status':'strict_structure_match','duplicate_status':'single_mp_alexmp20_exact_match','multiple_match_status':'not_applicable_at_D1','has_mp':True,'has_alexmp20':True,'in_d0_formula':True,'in_d1_mp_alexmp20_exact':True}); return denominator_base(o,'D1')
def d2(ds,audit):
    o=ds[['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); o['reduced_formula']=o.formula
    if len(audit): o=o.merge(audit[['material_id','official_alexandria_exact_matches','match_class']].rename(columns={'material_id':'mp_id'}),on='mp_id',how='left')
    o['match_status']='single_exact_match_triple_denominator'; o['duplicate_status']='single_match_retained'; o['multiple_match_status']=o.get('official_alexandria_exact_matches',pd.Series(1,index=o.index)).fillna(1).astype(int).map(lambda n:'single_match' if n==1 else 'multiple_match_excluded_or_tiebroken')
    for c in ['has_mp','has_alexmp20','has_alex_pbe','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match']: o[c]=True
    return denominator_base(o,'D2')
def d3(ds,jarvis):
    if len(jarvis):
        a=jarvis.groupby('material_id').agg(jarvis_match_count=('jarvis_jid','nunique'),jarvis_id=('jarvis_jid',lambda x:';'.join(sorted(set(map(str,x)))[:5]))).reset_index().rename(columns={'material_id':'mp_id'}); o=ds[['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].merge(a,on='mp_id',how='left')
    else: o=ds[['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); o['jarvis_match_count']=pd.NA
    o['has_jarvis']=o.jarvis_match_count.notna(); o['match_status']=o.has_jarvis.map({True:'jarvis_exact_structure_overlap',False:'no_jarvis_exact_match'}); o['duplicate_status']=o.jarvis_match_count.fillna(0).astype(int).map(lambda n:'no_match' if n==0 else ('single_match' if n==1 else 'multiple_match')); o['multiple_match_status']=o.duplicate_status
    for c in ['has_mp','has_alexmp20','has_alex_pbe','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match']: o[c]=True
    o['in_d3_jarvis_overlap']=o.has_jarvis; return denominator_base(o,'D3')
def d4(ds):
    o=ds[['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); o['match_status']='full_source_union_target_row'; o['duplicate_status']='not_applicable_source_union_pool'; o['multiple_match_status']='reported_in_source_union_status'; o['full_source_union_pool_status']='incomplete_until_full_phase_pool_reconstruction_available'
    for c in ['has_mp','has_alexmp20','has_alex_pbe','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match','in_d4_source_union_pool']: o[c]=True
    return denominator_base(o,'D4')
def d5(ds,scores):
    s=scores[scores.model.isin(MODELS)&scores.score_kind.eq('real_model_proxy_score')].dropna(subset=['score']); sets={m:set(g.row_id) for m,g in s.groupby('model')}; common=set.intersection(*(sets[m] for m in MODELS)); o=ds[ds.row_id.isin(common)][['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); o['match_status']='model_complete_intersection'; o['duplicate_status']='one_score_per_model_per_row_after_deduplication'; o['multiple_match_status']='not_applicable'
    for c in ['has_mp','has_alexmp20','has_alex_pbe','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match','in_d4_source_union_pool','in_d5_model_complete']: o[c]=True
    for m in MODELS: o[f'has_score_{m.lower().replace("-","_")}']=o.row_id.isin(sets.get(m,set()))
    return denominator_base(o,'D5')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,default=PHASE1_OUT); args=ap.parse_args(); out=ensure_dir(args.out); ensure_dir(out/'benchmark_cards')
    full=pd.read_csv(FULL,low_memory=False); triple=pd.read_csv(TRIPLE,low_memory=False); audit=pd.read_csv(AUDIT,low_memory=False) if AUDIT.exists() else pd.DataFrame(); jarvis=pd.read_csv(JARVIS,low_memory=False) if JARVIS.exists() else pd.DataFrame(); ds=pd.read_parquet(DATASET); scores=pd.read_csv(SCORES,low_memory=False)
    written=[sources_yaml(out),source_map(ds,out),fingerprints(ds,out),*write_source_cards(out)]
    for name,df in [('denominator_d0_formula.parquet',d0(full,triple,jarvis)),('denominator_d1_mp_alexmp20_exact.parquet',d1(full)),('denominator_d2_triple_single_match.parquet',d2(ds,audit)),('denominator_d3_jarvis_overlap.parquet',d3(ds,jarvis)),('denominator_d4_source_union_pool.parquet',d4(ds)),('denominator_d5_model_complete.parquet',d5(ds,scores))]: written.append(write_table(df,out/name))
    write_json({'expected_anchors':{'D1':43139,'D2':36802,'D5':36801}},out/'denominator_summary.json'); written.append(out/'denominator_summary.json'); write_manifest(out,list(out.rglob('*')),script='scripts/build_phase1_denominators.py'); return 0
if __name__=='__main__': raise SystemExit(main())
