#!/usr/bin/env python3
"""Build tie-aware source-native discovery curves for the locked v3 rankings."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'referee_revision_v3'
EVAL = OUT / 'evaluation'
FIG = OUT / 'figures'
SRC = OUT / 'figure_sources'
MODELS = ('ALIGNN-FF','CHGNet','M3GNet','MACE-MP')
ENDPOINTS = (
    ('official__mp_source_coordinate','MP native'),
    ('official__alexmp20_source_coordinate','alex-mp-20 native'),
    ('official__alex_pbe_source_coordinate','Alexandria-PBE native'),
)
COLORS = {'ALIGNN-FF':'#5B6FEA','CHGNet':'#D968A5','M3GNet':'#E7A933','MACE-MP':'#83C95A'}
STYLES = {
    'official__mp_source_coordinate':'solid',
    'official__alexmp20_source_coordinate':(0,(5,2.2)),
    'official__alex_pbe_source_coordinate':(0,(1.2,1.7)),
}


def tie_expected_curve(scores: np.ndarray, labels: np.ndarray, max_k: int) -> pd.DataFrame:
    """Analytic expected cumulative hits under exchangeability within score ties."""
    order=np.argsort(-scores,kind='mergesort')
    s=scores[order]
    y=labels[order].astype(int)
    rounded=np.round(s,12)
    starts=np.r_[0,1+np.flatnonzero(rounded[1:]!=rounded[:-1])]
    ends=np.r_[starts[1:],len(s)]
    expected=np.empty(max_k,dtype=float)
    tie_n=np.empty(max_k,dtype=int)
    hits_before=0.0
    for a,b in zip(starts,ends):
        if a>=max_k: break
        stop=min(b,max_k)
        block_n=b-a
        block_hits=int(y[a:b].sum())
        r=np.arange(1,stop-a+1,dtype=float)
        expected[a:stop]=hits_before+r*(block_hits/block_n)
        tie_n[a:stop]=block_n
        hits_before+=block_hits
    k=np.arange(1,max_k+1)
    return pd.DataFrame({'K':k,'expected_stable_hits':expected,'stable_yield':expected/k,'boundary_tie_n':tie_n})


def main() -> None:
    FIG.mkdir(parents=True,exist_ok=True); SRC.mkdir(parents=True,exist_ok=True)
    d=pd.read_parquet(EVAL/'mphys_fixed_support.parquet')
    max_k=min(10_000,len(d))
    rows=[]
    for model in MODELS:
        score=d[model].to_numpy(float)
        for endpoint,label in ENDPOINTS:
            y=d[endpoint].astype(int).to_numpy()
            curve=tie_expected_curve(score,y,max_k)
            curve['model_name']=model
            curve['coordinate_endpoint']=endpoint
            curve['endpoint_label']=label
            curve['positive_n']=int(y.sum())
            curve['support_n']=len(d)
            curve['recall']=curve.expected_stable_hits/int(y.sum())
            curve['ranking_estimand']='equivalence-class-excluded batch-relative transductive signed reference-hull margin'
            curve['tie_policy']='analytic expectation within rounded-12-decimal score ties'
            rows.append(curve)
    curves=pd.concat(rows,ignore_index=True)
    columns=['model_name','coordinate_endpoint','endpoint_label','K','support_n','positive_n','expected_stable_hits','stable_yield','recall','boundary_tie_n','ranking_estimand','tie_policy']
    curves=curves[columns]
    curves.to_parquet(SRC/'fig1_tie_aware_source_native_discovery_curves.parquet',index=False)
    curves[curves.K.isin([100,300,500,1000,5000,10000])].to_csv(SRC/'fig1_discovery_curve_budget_points.csv',index=False)

    plt.rcParams.update({
        'font.family':'DejaVu Sans','font.size':8.0,'axes.titlesize':9.5,
        'axes.labelsize':8.2,'xtick.labelsize':7.2,'ytick.labelsize':7.2,
        'axes.linewidth':0.7,'pdf.fonttype':42,'ps.fonttype':42,
        'savefig.facecolor':'white','axes.facecolor':'white',
    })
    fig,axes=plt.subplots(1,2,figsize=(7.35,3.15),gridspec_kw={'wspace':0.26})
    for ax,value,title,ylabel,letter in zip(
        axes,('stable_yield','recall'),('Discovery yield','Recovery'),
        ('Stable yield at $K$','Recall of source-defined stable set'),('a','b')):
        for model in MODELS:
            for endpoint,_ in ENDPOINTS:
                q=curves[curves.model_name.eq(model)&curves.coordinate_endpoint.eq(endpoint)]
                ax.plot(q.K,q[value],color=COLORS[model],linestyle=STYLES[endpoint],linewidth=1.35,alpha=0.96)
        ax.axvline(1000,color='#7A8390',linewidth=0.7,linestyle=(0,(4,3)),zorder=1)
        ax.text(1000,0.035,'1,000',transform=ax.get_xaxis_transform(),rotation=90,ha='right',va='bottom',fontsize=6.2,color='#65707D')
        ax.set_xlim(1,max_k)
        ax.set_xticks([0,2500,5000,7500,10000],['0','2.5k','5k','7.5k','10k'])
        ax.set_xlabel('Candidates validated, $K$')
        ax.set_ylabel(ylabel)
        ax.set_title(title,pad=4)
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',color='#D9DDE3',linewidth=0.55,zorder=0)
        ax.tick_params(length=3,width=0.6,color='#4A5058')
        ax.text(-0.13,1.04,letter,transform=ax.transAxes,fontweight='bold',fontsize=10)
    y=curves[curves.K.ge(50)].stable_yield
    axes[0].set_ylim(max(0,float(y.min())-0.04),min(1.0,float(y.max())+0.04))
    axes[1].set_ylim(0,float(curves.recall.max())*1.04)
    model_handles=[Line2D([0],[0],color=COLORS[m],lw=2.1,label=m) for m in MODELS]
    endpoint_handles=[Line2D([0],[0],color='#42484F',lw=1.5,linestyle=STYLES[e],label=l) for e,l in ENDPOINTS]
    fig.legend(model_handles+endpoint_handles,[h.get_label() for h in model_handles+endpoint_handles],
               ncol=4,loc='lower center',bbox_to_anchor=(0.5,-0.015),columnspacing=1.15,handlelength=2.4,fontsize=6.8,frameon=False)
    fig.subplots_adjust(bottom=0.27,left=0.085,right=0.99,top=0.91)
    fig.savefig(FIG/'fig1_revision_discovery_curves.pdf',bbox_inches='tight',pad_inches=0.02)
    fig.savefig(FIG/'fig1_revision_discovery_curves.tiff',dpi=600,bbox_inches='tight',pad_inches=0.02)
    plt.close(fig)
    print({'rows':len(curves),'max_k':max_k,'largest_boundary_tie_n':int(curves.boundary_tie_n.max())})

if __name__=='__main__':
    main()
