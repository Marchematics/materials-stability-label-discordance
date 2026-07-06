from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .io import PHASE1_OUT, ensure_dir, sha256_file, write_json
SCHEMA={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','required':['benchmark_name','benchmark_version','retained_denominator','source_coverage','pairwise_conflict_matrix','common_pool_status','full_source_union_status','consensus_stable_fraction','uncertain_fraction','metric_bands','topk_stable_yield_bands','manifest_sha256']}
def write_source_cards(out_dir=PHASE1_OUT):
    cd=ensure_dir(Path(out_dir)/'benchmark_cards'); common={'stable_threshold':'e_above_hull <= 1e-8 eV/atom','duplicate_handling':'single exact matches retained; multiple matches audited','missing_id_handling':'missing IDs excluded from exact denominators','exact_match_handling':'structure exact denominators are separate from D0 formula overlap','unmatched_handling':'unmatched rows counted in audit fields'}
    specs={'source_mp.json':('Materials Project','source_native_mp_label','source_native_mp_ehull',True,True),'source_alexmp20.json':('MatterGen alex-mp-20','source_native_mattergen_label','source_native_mattergen_ehull',False,False),'source_alex_pbe.json':('official Alexandria-PBE','source_native_alexandria_label','source_native_alexandria_ehull',True,True),'source_jarvis.json':('JARVIS-DFT 3D','jarvis_stable_exact','jarvis_ehull',False,False)}
    paths=[]
    for fn,(name,l,h,fe,can) in specs.items():
        paths.append(write_json({**common,'source_name':name,'version_or_snapshot_date':'archived public snapshot or milestone cache','query_or_download_date':'archived in milestone outputs','label_field_name':l,'hull_stability_field':h,'unit':'eV/atom','formation_energy_available':fe,'can_enter_common_pool_or_source_union_hull':can},cd/fn))
    return paths
def _conf(labels,a,b):
    m=labels[labels.label_view.eq(a)][['row_id','label']].rename(columns={'label':'a'}).merge(labels[labels.label_view.eq(b)][['row_id','label']].rename(columns={'label':'b'}),on='row_id').dropna()
    if m.empty: return {'n':0,'conflict_n':0,'conflict_fraction':None,'a_stable_b_unstable':0,'a_unstable_b_stable':0}
    aa=m.a.astype(bool); bb=m.b.astype(bool); c=aa!=bb
    return {'n':len(m),'conflict_n':int(c.sum()),'conflict_fraction':float(c.mean()),'a_stable_b_unstable':int((aa&~bb).sum()),'a_unstable_b_stable':int((~aa&bb).sum())}
def generate_card(labels_path, metrics_path, out=PHASE1_OUT/'benchmark_card_main.json'):
    out=Path(out); ensure_dir(out.parent); labels=pd.read_parquet(labels_path); metrics=pd.read_csv(metrics_path) if Path(metrics_path).exists() else pd.DataFrame()
    d2=len(pd.read_parquet(out.parent/'denominator_d2_triple_single_match.parquet')) if (out.parent/'denominator_d2_triple_single_match.parquet').exists() else labels.row_id.nunique(); d5=len(pd.read_parquet(out.parent/'denominator_d5_model_complete.parquet')) if (out.parent/'denominator_d5_model_complete.parquet').exists() else 0
    su=json.loads((out.parent/'source_union_hull_status.json').read_text()) if (out.parent/'source_union_hull_status.json').exists() else {'status':'missing'}
    conflicts={f'{a}__vs__{b}':_conf(labels,a,b) for a,b in [('mp_native','alexmp20_native'),('mp_native','alex_pbe_native'),('alexmp20_native','alex_pbe_native'),('mp_common_pool','alex_pbe_common_pool')]}
    source_cov={k:{kk:int(vv) for kk,vv in v.items()} for k,v in labels.groupby('label_view').agg(n=('row_id','nunique'),evaluable=('is_evaluable','sum')).to_dict('index').items()}
    cons=labels[labels.label_view.eq('consensus_stable')]; unc=labels[labels.label_view.eq('uncertain')]
    mb={}
    if not metrics.empty:
        for m in ['auroc','auprc','f1','balanced_accuracy']:
            v=pd.to_numeric(metrics[m],errors='coerce').dropna() if m in metrics else pd.Series(dtype=float)
            if len(v): mb[m]={'min':float(v.min()),'max':float(v.max()),'spread':float(v.max()-v.min())}
    tb={}; tp=out.parent/'topk_yield_by_label_view.csv'
    if tp.exists():
        top=pd.read_csv(tp)
        for k,g in top.groupby('K'):
            v=g.stable_fraction.dropna(); tb[str(k)]={'min':float(v.min()),'max':float(v.max()),'spread':float(v.max()-v.min())}
    manifest=out.parent/'manifest_phase1_v2.json'
    card={'benchmark_name':'SourceAware-Stability phase1_v2','benchmark_version':'phase1_v2','framing':'Source-aware crystal-stability evaluation is a benchmark-layer problem, not a single-label database comparison.','retained_denominator':{'D2_SourceAware_Stability_36K':d2,'D5_model_complete':d5},'source_coverage':source_cov,'pairwise_conflict_matrix':conflicts,'directionality':{k:{'first_stable_second_unstable':v['a_stable_b_unstable'],'first_unstable_second_stable':v['a_unstable_b_stable']} for k,v in conflicts.items()},'near_threshold_burden':{},'common_pool_status':{'status':'available','scope':'matched-denominator common pool; MatterGen not reconstructed'},'full_source_union_status':su,'consensus_stable_fraction':float(cons.label.fillna(False).astype(bool).mean()),'uncertain_fraction':float(unc.label.astype(bool).mean()),'metric_bands':mb,'topk_stable_yield_bands':tb,'manifest_sha256':sha256_file(manifest) if manifest.exists() else ''}
    write_json(SCHEMA,out.parent/'benchmark_card_schema.json'); write_json(card,out); out.with_suffix('.md').write_text(f"# {card['benchmark_name']} benchmark card\n\nD2={d2}; D5={d5}. Full-source-union status: {su.get('status')}.\n",encoding='utf-8'); return card
