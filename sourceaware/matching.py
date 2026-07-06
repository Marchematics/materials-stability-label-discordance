from __future__ import annotations
import pandas as pd
from .io import sha256_text
def row_hash(*xs): return sha256_text('|'.join('' if pd.isna(x) else str(x) for x in xs))
def bool_series(s):
    if str(s.dtype)=='boolean' or s.dtype==bool: return s.astype('boolean')
    return s.astype(str).str.lower().isin(['true','1','yes']).astype('boolean')
def stable_from_ehull(s, tol=1e-8): return pd.to_numeric(s,errors='coerce').le(tol).astype('boolean')
def denominator_base(df,prefix):
    out=df.copy()
    if 'row_id' not in out: out.insert(0,'row_id',[f'{prefix}-{i:05d}' for i in range(1,len(out)+1)])
    if 'reduced_formula' not in out and 'formula' in out: out['reduced_formula']=out['formula'].astype(str)
    if 'structure_hash' not in out: out['structure_hash']=[row_hash(prefix,i) for i in range(len(out))]
    for c in ['match_status','duplicate_status','multiple_match_status']:
        if c not in out: out[c]='not_reported'
    for c in ['has_mp','has_alexmp20','has_alex_pbe','has_jarvis','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match','in_d3_jarvis_overlap','in_d4_source_union_pool','in_d5_model_complete']:
        if c not in out: out[c]=False
    first=['row_id','mp_id','mattergen_id','official_alexandria_id','jarvis_id','formula','reduced_formula','chemical_system','structure_hash','match_status','duplicate_status','multiple_match_status','has_mp','has_alexmp20','has_alex_pbe','has_jarvis','in_d0_formula','in_d1_mp_alexmp20_exact','in_d2_triple_single_match','in_d3_jarvis_overlap','in_d4_source_union_pool','in_d5_model_complete']
    return out[[c for c in first if c in out]+[c for c in out.columns if c not in first]]
