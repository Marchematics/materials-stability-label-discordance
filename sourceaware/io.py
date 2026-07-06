from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Iterable
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
PHASE1_OUT=ROOT/'outputs'/'phase1_v2'
def ensure_dir(p):
    p=Path(p); p.mkdir(parents=True,exist_ok=True); return p
def sha256_file(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
def sha256_text(s:str)->str: return hashlib.sha256(s.encode()).hexdigest()
def read_table(p, **kw):
    p=Path(p)
    return pd.read_parquet(p,**kw) if p.suffix=='.parquet' else pd.read_csv(p,low_memory=False,**kw)
def write_table(df,p):
    p=Path(p); ensure_dir(p.parent)
    if p.suffix=='.parquet': df.to_parquet(p,index=False)
    elif p.suffix=='.csv': df.to_csv(p,index=False)
    else: p.write_text(df.to_json(orient='records',indent=2),encoding='utf-8')
    return p
def write_json(o,p):
    p=Path(p); ensure_dir(p.parent); p.write_text(json.dumps(o,indent=2,sort_keys=True),encoding='utf-8'); return p
def manifest_record(p, script=None):
    p=Path(p)
    rows=cols=None
    try:
        df=read_table(p); rows=len(df); cols=len(df.columns)
    except Exception: pass
    
    try:
        rel=str(p.resolve().relative_to(ROOT))
    except Exception:
        rel=str(p)
    return {'path':rel,'sha256':sha256_file(p),'bytes':p.stat().st_size,'rows':rows,'columns':cols,'generating_script':script}
def write_manifest(out_dir, paths:Iterable, name='manifest_phase1_v2.json', script=None):
    paths=[Path(p) for p in paths]
    excluded={name,'benchmark_card_main.json','benchmark_card_main.md'}
    rec=[manifest_record(p,script) for p in sorted(paths,key=str) if p.exists() and p.is_file() and p.name not in excluded]
    return write_json({'benchmark_layer':'SourceAware-Stability phase1_v2','manifest_version':'1.0','file_count':len(rec),'files':rec}, Path(out_dir)/name)
