from __future__ import annotations
from itertools import combinations
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score, f1_score, precision_score, recall_score
from .io import ROOT, PHASE1_OUT, ensure_dir, read_table, write_table
SCORES=ROOT/'outputs/milestones/model_leaderboard_impact/model_scores_public_safe.csv'; MODELS=['ALIGNN-FF','CHGNet','MACE-MP','M3GNet']; K_GRID=[100,300,500,1000,5000]
def safe(fn,y,s):
    try: return float(fn(y,s)) if len(set(y))>1 else np.nan
    except Exception: return np.nan
def thresh(score,y):
    n=int(y.sum()); ids=set(score.sort_values(ascending=False,kind='mergesort').head(n).index); return np.array([i in ids for i in score.index],bool)
def load_model_complete_scores():
    s=read_table(SCORES); s=s[s.model.isin(MODELS)&s.score_kind.eq('real_model_proxy_score')].copy(); s['score']=pd.to_numeric(s.score,errors='coerce'); s=s.dropna(subset=['score']); sets={m:set(g.row_id) for m,g in s.groupby('model')}; common=set.intersection(*(sets[m] for m in MODELS)); return s[s.row_id.isin(common)].copy()
def compute_model_metrics(labels_path, out_dir=PHASE1_OUT):
    out_dir=ensure_dir(out_dir); labels=pd.read_parquet(labels_path); scores=load_model_complete_scores(); views=labels[(labels.label_semantics=='stability')]
    mrows=[]; trows=[]
    for (model,src),sf in scores.groupby(['model','score_source']):
        sf=sf[['row_id','score','model','model_version','score_source','score_kind']]
        for view,ldf in views.groupby('label_view'):
            mg=sf.merge(ldf[ldf.is_evaluable][['row_id','label','is_uncertain']],on='row_id')
            if mg.empty: continue
            y=mg.label.astype(bool).astype(int).to_numpy(); sc=mg.score.astype(float).to_numpy(); idx=mg.set_index('row_id'); pred=thresh(idx.score,idx.label.astype(bool))
            mrows.append({'model':model,'model_version':str(mg.model_version.iloc[0]),'score_source':src,'score_kind':str(mg.score_kind.iloc[0]),'label_view':view,'n':len(mg),'positive_rate':float(np.mean(y)),'auroc':safe(roc_auc_score,y,sc),'auprc':safe(average_precision_score,y,sc),'balanced_accuracy':float(balanced_accuracy_score(y,pred)) if len(set(y))>1 else np.nan,'f1':float(f1_score(y,pred,zero_division=0)),'precision_threshold_matched':float(precision_score(y,pred,zero_division=0)),'recall_threshold_matched':float(recall_score(y,pred,zero_division=0)),'model_complete_denominator_n':scores.row_id.nunique()})
            rank=mg.sort_values('score',ascending=False,kind='mergesort')
            for k in K_GRID:
                top=rank.head(min(k,len(rank))); trows.append({'model':model,'label_view':view,'K':k,'n_ranked':len(rank),'stable_n':int(top.label.astype(bool).sum()),'stable_fraction':float(top.label.astype(bool).mean()),'uncertain_fraction':float(top.is_uncertain.astype(bool).mean())})
    metrics=pd.DataFrame(mrows); topk=pd.DataFrame(trows); write_table(metrics,out_dir/'model_metrics_by_label_view.csv'); write_table(topk,out_dir/'topk_yield_by_label_view.csv')
    bands=[]
    for metric in ['auroc','auprc','f1','balanced_accuracy']:
        for model,sub in metrics.groupby('model'):
            v=pd.to_numeric(sub[metric],errors='coerce').dropna();
            if len(v): bands.append({'scope':'within_model_across_label_views','model':model,'metric':metric,'min':v.min(),'max':v.max(),'spread':v.max()-v.min()})
        for view,sub in metrics.groupby('label_view'):
            v=pd.to_numeric(sub[metric],errors='coerce').dropna();
            if len(v): bands.append({'scope':'within_label_view_across_models','label_view':view,'metric':metric,'min':v.min(),'max':v.max(),'spread':v.max()-v.min()})
    bands=pd.DataFrame(bands); write_table(bands,out_dir/'label_view_band_vs_model_spread.csv')
    audit=labels[labels.label_view.eq('audit_view')][['row_id','is_uncertain']]; u=[]
    for model,sf in scores.groupby('model'):
        r=sf.merge(audit,on='row_id').sort_values('score',ascending=False,kind='mergesort')
        for k in K_GRID:
            top=r.head(k); u.append({'model':model,'K':k,'n':len(top),'uncertain_n':int(top.is_uncertain.astype(bool).sum()),'uncertain_fraction':float(top.is_uncertain.astype(bool).mean())})
    unc=pd.DataFrame(u); write_table(unc,out_dir/'uncertain_fraction_by_topk.csv')
    inv=[]
    for metric in ['auroc','auprc','f1']:
        ranks={v:g.dropna(subset=[metric]).sort_values(metric,ascending=False).model.tolist() for v,g in metrics.groupby('label_view')}
        for a,b in combinations(sorted(ranks),2):
            common=[m for m in ranks[a] if m in ranks[b]]
            if len(common)>1:
                ra={m:i for i,m in enumerate(ranks[a])}; rb={m:i for i,m in enumerate(ranks[b])}; d=sum(1 for x,y in combinations(common,2) if (ra[x]-ra[y])*(rb[x]-rb[y])<0); inv.append({'metric':metric,'label_view_a':a,'label_view_b':b,'common_model_n':len(common),'pairwise_rank_inversions':d,'top_model_a':ranks[a][0],'top_model_b':ranks[b][0],'leading_model_overturned':ranks[a][0]!=ranks[b][0]})
    inv=pd.DataFrame(inv); write_table(inv,out_dir/'model_rank_inversions.csv'); return {'metrics':metrics,'topk':topk,'bands':bands,'uncertain':unc,'inversions':inv}
