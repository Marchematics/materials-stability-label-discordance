from __future__ import annotations
from pathlib import Path
import pandas as pd
from .io import ROOT, PHASE1_OUT, ensure_dir, write_table
DATASET=ROOT/'outputs/SourceAware-Stability-36K/sourceaware_stability_36k.parquet'
def add(rows,base,view,label,sem='stability',uncertain=False,source=''):
    d=base.copy(); d['label_view']=view; d['label']=label.astype('boolean') if hasattr(label,'astype') else label; d['is_uncertain']=uncertain.astype('boolean') if hasattr(uncertain,'astype') else bool(uncertain); d['label_semantics']=sem; d['label_source']=source or view; d['is_evaluable']=d.label.notna(); rows.append(d)
def build_label_views(out_dir=PHASE1_OUT):
    out_dir=ensure_dir(out_dir); ds=pd.read_parquet(DATASET); base=ds[['row_id','mp_id','mattergen_id','official_alexandria_id','formula','chemical_system','structure_hash']].copy(); rows=[]
    add(rows,base,'mp_native',ds.source_native_mp_label,source='MP native')
    add(rows,base,'alexmp20_native',ds.source_native_mattergen_label,source='MatterGen alex-mp-20 native')
    add(rows,base,'alex_pbe_native',ds.source_native_alexandria_label,source='official Alexandria-PBE native')
    add(rows,base,'mp_common_pool',ds.common_pool_mp_label,source='MP matched common pool')
    add(rows,base,'alex_pbe_common_pool',ds.common_pool_alexandria_label,source='Alexandria matched common pool')
    cp_mp=ds.common_pool_mp_label.astype('boolean'); cp_ax=ds.common_pool_alexandria_label.astype('boolean')
    cp_agree=cp_mp.notna() & cp_ax.notna() & (cp_mp==cp_ax)
    cp_label=cp_mp.where(cp_agree, pd.NA).astype('boolean')
    add(rows,base,'common_pool',cp_label,uncertain=~cp_agree,source='MP/Alexandria matched common-pool consensus when both common-pool labels agree')
    su_path=out_dir/'source_union_hull_labels.parquet'
    if su_path.exists():
        su=pd.read_parquet(su_path).set_index('row_id'); mp=su.reindex(ds.row_id).full_source_union_mp_label.reset_index(drop=True); ax=su.reindex(ds.row_id).full_source_union_alex_pbe_label.reset_index(drop=True)
    else:
        mp=pd.Series(pd.NA,index=ds.index,dtype='boolean'); ax=mp.copy()
    add(rows,base,'mp_full_source_union',mp,source='MP full-source-union diagnostic')
    add(rows,base,'alex_pbe_full_source_union',ax,source='Alexandria full-source-union diagnostic')
    su_agree=mp.notna() & ax.notna() & (mp.astype('boolean')==ax.astype('boolean'))
    su_label=mp.astype('boolean').where(su_agree, pd.NA).astype('boolean')
    add(rows,base,'source_union',su_label,uncertain=~su_agree,source='full-source-union consensus when reconstruction is complete and MP/Alexandria source-union labels agree')
    nat=ds[['source_native_mp_label','source_native_mattergen_label','source_native_alexandria_label']].astype(bool); agree=nat.nunique(axis=1).eq(1); add(rows,base,'all_source_native',nat.source_native_mp_label.where(agree,pd.NA).astype('boolean'),uncertain=~agree,source='unanimous native labels')
    eval_=ds.consensus_label.isin(['consensus_stable','consensus_unstable']); cons=ds.consensus_label.eq('consensus_stable').where(eval_,pd.NA).astype('boolean'); add(rows,base,'consensus',cons,uncertain=~eval_,source='strict source-aware consensus')
    add(rows,base,'consensus_stable',cons,uncertain=~eval_,source='strict consensus')
    uncertain=~eval_; add(rows,base,'uncertain',uncertain.astype('boolean'),sem='uncertainty_indicator',uncertain=uncertain,source='uncertainty indicator')
    add(rows,base,'audit_view',ds.consensus_label.eq('consensus_stable').astype('boolean'),uncertain=uncertain,source='audit positive consensus stable')
    out=pd.concat(rows,ignore_index=True); meta=ds.set_index('row_id')[['source_native_mp_ehull','source_native_mattergen_ehull','source_native_alexandria_ehull','common_pool_mp_ehull','common_pool_alexandria_ehull','consensus_label','uncertainty_class','uncertainty_reason']]
    out=out.merge(meta,left_on='row_id',right_index=True,how='left'); write_table(out,out_dir/'labels_by_view.parquet'); return out
