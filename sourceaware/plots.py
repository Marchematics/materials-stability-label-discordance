from __future__ import annotations
from pathlib import Path
import pandas as pd
from .io import PHASE1_OUT, ensure_dir
def build_figure_source_data(out_dir=PHASE1_OUT):
    out_dir=Path(out_dir); fd=ensure_dir(out_dir/'figure_source_data'); figs=ensure_dir(out_dir/'figures'); paths=[]
    for name,src in [('fig1_model_label_uncertainty_metrics.csv','model_metrics_by_label_view.csv'),('fig1_topk_uncertainty.csv','topk_yield_by_label_view.csv'),('fig3_conflict_decomposition.csv','conflict_decomposition.csv')]:
        p=fd/name; pd.read_csv(out_dir/src).to_csv(p,index=False); paths.append(p)
    rows=[]
    for p in sorted(out_dir.glob('denominator_d*.parquet')):
        df=pd.read_parquet(p); rows.append({'denominator':p.stem,'n':len(df),'columns':len(df.columns)})
    p=fd/'fig2_denominator_hierarchy.csv'; pd.DataFrame(rows).to_csv(p,index=False); paths.append(p)
    labels=pd.read_parquet(out_dir/'labels_by_view.parquet'); one=labels[labels.label_view.eq('mp_native')]; vals=one[['source_native_mp_ehull','source_native_mattergen_ehull','source_native_alexandria_ehull','common_pool_mp_ehull','common_pool_alexandria_ehull']].apply(pd.to_numeric,errors='coerce')
    p=fd/'fig4_near_threshold_diagnostics.csv'; pd.DataFrame([{'threshold_mev_atom':m,'flagged_n':int(vals.abs().le(m/1000).any(axis=1).sum()),'denominator_n':len(vals)} for m in [1,5,10,25]]).to_csv(p,index=False); paths.append(p)
    p=fd/'fig5_workflow_card_inputs.csv'; pd.DataFrame([{'step':'benchmark card','artifact':'benchmark_card_main.json'}]).to_csv(p,index=False); paths.append(p)
    p=fd/'fig6_jarvis_portability.csv'; pd.read_parquet(out_dir/'denominator_d3_jarvis_overlap.parquet').to_csv(p,index=False); paths.append(p)
    r=figs/'README.md'; r.write_text('# Phase 1 v2 figures\nSource data are in ../figure_source_data/.\n',encoding='utf-8'); paths.append(r); return paths
