"""Redraw manuscript Figures 2--5 from frozen data; no model or DFT calculations."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--package-root',type=Path);parser.add_argument('--output',type=Path)
args=parser.parse_args()
if args.package_root:
 root=args.package_root.resolve();SRC=root/'06_source_data/figure_source_tables';DATA=root/'06_source_data/analysis_outputs';LABELS=DATA/'row_level_hull_distance_labels.parquet'
else:
 root=P.parent;SRC=root/'outputs/publication/figure_source_tables';DATA=root/'outputs/referee_revision_v3';LABELS=DATA/'row_level_hull_distance_labels.parquet'
OUT=(args.output or root/'manuscript/figures').resolve();OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7.5,'axes.titlesize':8.2,'axes.labelsize':7.4,'xtick.labelsize':6.8,'ytick.labelsize':6.8,'legend.fontsize':7,'axes.linewidth':.65,'lines.linewidth':1.35,'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
MODELS=['ALIGNN-FF','CHGNet','M3GNet','MACE-MP'];MC=dict(zip(MODELS,['#0072B2','#E69F00','#009E73','#CC79A7']))
ENDS=['mp_source_coordinate','alexmp20_source_coordinate','alex_pbe_source_coordinate','mp_matched_pool_coordinate','alex_pbe_matched_pool_coordinate']
SHORT=['MP','alex-mp-20','Alexandria','MP shared','Alex. shared'];EC=['#0072B2','#009E73','#D55E00']
GREEN='#009E73';ORANGE='#D55E00';PURPLE='#8C6BB1';GRAY='#BBC2C7'
inputs={}
layout_checks={}
def read(path):
 inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 return pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path)
def panel(ax,letter,title):
 ax.set_title(title,loc='left',pad=10,fontweight='semibold');ax.annotate(letter,xy=(0,1),xycoords='axes fraction',xytext=(-18,10),textcoords='offset points',fontweight='bold',fontsize=11,va='bottom');ax.tick_params(direction='out',width=.6,length=2.5)
def save(fig,name):
 fig.canvas.draw()
 renderer=fig.canvas.get_renderer(); bounds=fig.bbox
 outside=[]
 for artist in fig.findobj(match=matplotlib.text.Text):
  if not artist.get_visible() or not artist.get_text():continue
  box=artist.get_window_extent(renderer)
  if box.x0 < -2 or box.y0 < -2 or box.x1 > bounds.width+2 or box.y1 > bounds.height+2:outside.append(artist.get_text())
 layout_checks[name]={'text_outside_canvas':outside}
 if outside:raise ValueError((name,outside))
 for ext in ['pdf','svg','png','tiff']:
  kw={'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tiff' else {}
  fig.savefig(OUT/f'{name}.{ext}',dpi=600,**kw)
  if ext=='svg':
   path=OUT/f'{name}.{ext}';path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()).rstrip()+'\n')
 plt.close(fig)
def source(df,name):df.to_csv(OUT/name,index=False)

labels=read(LABELS);assert len(labels)==36802
threshold=read(SRC/'fig2_threshold_scan.source.csv')
strata=read(SRC/'fig3_materials_chemistry_strata.source.csv')
decomp=read(DATA/'evaluation/common_pool_decomposition_threshold_scan.csv');decomp=decomp[decomp.support.eq('D2') & decomp.threshold_meV_per_atom.le(50)].copy()
ind=read(DATA/'evaluation/indeterminate_zone_conflicts.csv');ind=ind[ind.support.eq('D2_reconstructable') & ind.endpoint_a.eq('mp_source_coordinate') & ind.endpoint_b.eq('alex_pbe_source_coordinate')].copy().sort_values('indeterminate_width_meV_per_atom')
hits=read(SRC/'fig4_hits_at_1000.csv');hits=hits[hits.threshold_meV_per_atom.eq(0)&hits.K.eq(1000)].copy()
metrics=read(DATA/'evaluation/metrics_physical_endpoints.csv');metrics=metrics[metrics.threshold_meV_per_atom.eq(0)].copy()
curves=read(SRC/'fig1_sourceaware_discovery_curves.full.parquet')

# Figure 2: the same density and threshold view for all three source pairs.
columns=['source_native_mp_ehull','source_native_mattergen_ehull','source_native_alexandria_ehull']
names=['MP','alex-mp-20','Alexandria-PBE'];pairs=[(0,1),(0,2),(1,2)];counts=[4244,5666,3862]
fig,axs=plt.subplots(2,3,figsize=(7.2,5.1));fig.subplots_adjust(left=.075,right=.93,bottom=.11,top=.86,wspace=.44,hspace=.55)
xy=[np.clip(labels[columns].to_numpy(float)[:,[a,b]]*1000,0,120) for a,b in pairs]
maxbin=max(np.histogram2d(v[:,0],v[:,1],bins=42,range=[[0,120],[0,120]])[0].max() for v in xy)
for j,((a,b),v) in enumerate(zip(pairs,xy)):
 ax=axs[0,j];conflict=(labels[columns[a]].le(1e-12)!=labels[columns[b]].le(1e-12)).to_numpy();assert int(conflict.sum())==counts[j]
 im=ax.hist2d(v[:,0],v[:,1],bins=42,range=[[0,120],[0,120]],norm=LogNorm(1,maxbin),cmap='Blues',cmin=1,rasterized=True)[3]
 ax.scatter(v[conflict,0],v[conflict,1],s=2.2,color=ORANGE,alpha=.28,linewidths=0,rasterized=True)
 ax.plot([0,120],[0,120],':',color='#677685',lw=.9);ax.set(xlim=(-2,122),ylim=(-2,122),xticks=[0,40,80,120],yticks=[0,40,80,120]);ax.set_aspect('equal')
 if j==0:
  ax.axhline(100,color='#7A7A7A',ls='--',lw=.7);ax.set_yticks([0,40,80,100,120])
 if j==2:
  ax.axvline(100,color='#7A7A7A',ls='--',lw=.7);ax.set_xticks([0,40,80,100,120])
 ax.set_xlabel(names[a]+r' $E_{\rm hull}$ (meV atom$^{-1}$)');ax.set_ylabel(names[b]+r' $E_{\rm hull}$ (meV atom$^{-1}$)')
 panel(ax,'abc'[j],['MP vs alex-mp-20','MP vs Alexandria','alex-mp-20 vs Alex.'][j]);ax.text(.05,.94,f'{counts[j]/36802*100:.1f}% switch at 0 meV',transform=ax.transAxes,va='top',fontsize=7,color='#A53D00',bbox={'fc':'white','ec':'none','alpha':.9,'pad':2})
 ax=axs[1,j];d=threshold[(threshold.endpoint_a==ENDS[a])&(threshold.endpoint_b==ENDS[b])].sort_values('threshold_meV_per_atom');assert len(d)==4
 x=d.threshold_meV_per_atom.to_numpy();y=d.switch_rate.to_numpy()*100
 ax.fill_between(x,d.switch_rate_ci_low_95.to_numpy()*100,d.switch_rate_ci_high_95.to_numpy()*100,color=EC[j],alpha=.16,lw=0)
 ax.plot(x,y,'o-',color=EC[j],ms=3);ax.set(xlim=(-2,52),ylim=(5,17.5),xticks=[0,10,25,50],yticks=[5,10,15]);ax.grid(axis='y',color='#E7EBEF',lw=.5)
 ax.set_xlabel(r'Threshold (meV atom$^{-1}$)');ax.set_ylabel('Label switches (%)');panel(ax,'def'[j],'Threshold sensitivity')
 for k in [0,3]:ax.annotate(f'{y[k]:.1f}%',(x[k],y[k]),xytext=(3,8),textcoords='offset points',fontsize=7,color=EC[j],ha='left' if k==0 else 'right')
cax=fig.add_axes([.954,.563,.011,.32]);cb=fig.colorbar(im,cax=cax);cb.set_ticks([1,10,100,1000,10000]);cb.minorticks_off();cb.ax.tick_params(labelsize=6,length=2)
fig.text(.075,.974,'Same structures, three stability-reference comparisons',fontsize=10,fontweight='bold')
fig.text(.075,.944,'36,802 matched structures · common axes and density scale',fontsize=7.5,color='#50606B')
pointdata=labels[['row_id',*columns]].copy();source(pointdata,'fig2_three_source_hull_coordinates.source.csv');save(fig,'fig2_near_threshold_discordance')

# Figure 3: one chemical question per small panel, with a common rate scale.
fig=plt.figure(figsize=(7.2,3.35));gs=fig.add_gridspec(2,3,width_ratios=[1.22,1,1],left=.18,right=.97,bottom=.16,top=.81,wspace=.52,hspace=.86)
axes=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[0,1]),fig.add_subplot(gs[0,2]),fig.add_subplot(gs[1,1]),fig.add_subplot(gs[1,2])]
groups=[['Unary','Binary','Ternary','Quaternary+'],['Oxygen','No oxygen'],['Halogen','No halogen'],['Lanthanide','No lanthanide'],['Transition metal','No transition metal']]
titles=['Chemical complexity','Oxygen','Halogen','Lanthanide','Transition metal'];baseline=5666/36802*100
for i,(ax,g,title) in enumerate(zip(axes,groups,titles)):
 d=strata.set_index('stratum').loc[g];y=np.arange(len(g))[::-1];rates=d.discordance_rate.to_numpy()*100;lo=d.ci_low_95.to_numpy()*100;hi=d.ci_high_95.to_numpy()*100
 ax.axvline(baseline,color='#6D7782',ls='--',lw=.9,zorder=0)
 for yy,r,l,h in zip(y,rates,lo,hi):ax.errorbar(r,yy,xerr=[[r-l],[h-r]],fmt='o',color=ORANGE if r>baseline else '#497C9B',ms=4,capsize=2,lw=1)
 labs=[f'{v}\n(n={n:,})' for v,n in zip(g,d.row_n)] if i==0 else [f'Present\n(n={int(d.row_n.iloc[0]):,})',f'Absent\n(n={int(d.row_n.iloc[1]):,})']
 ax.set(yticks=y,yticklabels=labs,xlim=(0,25),xticks=[0,10,20],ylim=(-.5,len(g)-.5));ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#E7EBEF',lw=.5);panel(ax,'abcde'[i],title)
 if i in [0,3,4]:ax.set_xlabel('Label switches (%)')
 for yy,r in zip(y,rates):ax.text(25,yy,f'{r:.1f}',ha='right',va='center',fontsize=6.8,color='#36424D')
fig.text(.075,.96,'Chemical regimes differ in label sensitivity',fontsize=10,fontweight='bold')
fig.text(.075,.91,'MP / Alexandria-PBE · 0 meV threshold · dashed line: overall rate (15.4%)',fontsize=7.5,color='#50606B')
save(fig,'fig3_sourceaware_benchmark_layer')

# Figure 4: repeated before/after comparisons, inspired by the supplied
# figures4papers/figure_Brainteaser layouts. No isolated count cards or pies.
complete=labels.dropna(subset=['common_pool_mp_ehull','common_pool_alexandria_ehull']).copy()
assert len(complete)==36770
complexity=complete.chemical_system.str.split('-').map(len).clip(upper=4)
phase_rows=[]
for t in [0,10,25,50]:
 cut=1e-12 if t==0 else t/1000
 native=complete.source_native_mp_ehull.le(cut)!=complete.source_native_alexandria_ehull.le(cut)
 shared=complete.common_pool_mp_ehull.le(cut)!=complete.common_pool_alexandria_ehull.le(cut)
 expected=decomp[decomp.threshold_meV_per_atom.eq(t)].iloc[0]
 assert int(native.sum())==int(expected.reconstructable_native_conflict_n)
 assert int(shared.sum())==int(expected.common_pool_conflict_n)
 assert int((native & ~shared).sum())==int(expected.phase_pool_sensitive_n)
 assert int((native & shared).sum())==int(expected.persistent_conflict_n)
 assert int((~native & shared).sum())==int(expected.hidden_common_pool_conflict_n)
 for k in [1,2,3,4]:
  mask=complexity.eq(k);n=int(mask.sum())
  for name,conflict in [('Original',native),('Shared inventory',shared)]:
   count=int(conflict[mask].sum());phase_rows.append({'threshold_meV_per_atom':t,'elements_group':str(k) if k<4 else '4+','inventory':name,'n':n,'conflicts':count,'disagreement_percent':count/n*100})
phase_rows=pd.DataFrame(phase_rows)
fig=plt.figure(figsize=(7.2,4.85));gs=fig.add_gridspec(2,4,left=.085,right=.98,bottom=.14,top=.90,wspace=.55,hspace=.66,height_ratios=[1,1.1])
comparison_axes=[fig.add_subplot(gs[0,j]) for j in range(4)]
complexity_colors=['#86C980','#E5A09B','#F5DE9B','#3E7DB6']
for i,(ax,t) in enumerate(zip(comparison_axes,[0,10,25,50])):
 d=phase_rows[phase_rows.threshold_meV_per_atom.eq(t)]
 for j,group in enumerate(['1','2','3','4+']):
  for offset,inventory,hatch in [(-.18,'Original',''),(.18,'Shared inventory','///')]:
   row=d[d.elements_group.eq(group)&d.inventory.eq(inventory)].iloc[0]
   ax.bar(j+offset,row.disagreement_percent,width=.33,color=complexity_colors[j],edgecolor='#303030',lw=.45,hatch=hatch,zorder=3)
 ax.set(xticks=np.arange(4),xticklabels=['1','2','3','4+'],ylim=(0,25),yticks=[0,5,10,15,20,25])
 ax.set_xlabel('Elements per formula');ax.set_ylabel('Label disagreement (%)' if i==0 else '')
 ax.set_title(f'{t} meV atom'+r'$^{-1}$',fontweight='normal',fontsize=9.5,pad=10)
 ax.annotate('abcd'[i],xy=(0,1),xycoords='axes fraction',xytext=(-16,10),textcoords='offset points',fontweight='bold',fontsize=10,va='bottom')
 ax.tick_params(length=2,width=.6)
 if i>0:ax.tick_params(axis='y',labelleft=False)
fig.legend(handles=[Patch(facecolor='white',edgecolor='#303030',label='Original reference'),Patch(facecolor='white',edgecolor='#303030',hatch='///',label='Shared phase inventory')],loc='upper center',bbox_to_anchor=(.53,1.005),ncol=2,frameon=False,fontsize=8,handlelength=2)
ax=fig.add_subplot(gs[1,:2])
for col,color,label in [('phase_pool_sensitive_n','#86C980','Resolved'),('persistent_conflict_n','#E5A09B','Persistent'),('hidden_common_pool_conflict_n','#3E7DB6','Newly exposed')]:
 ax.plot(decomp.threshold_meV_per_atom,decomp[col],marker='o',color=color,ms=4,lw=1.7,label=label)
ax.set(xticks=[0,10,25,50],ylim=(0,4200),yticks=[0,1000,2000,3000,4000]);ax.set_xlabel(r'Stability threshold (meV atom$^{-1}$)');ax.set_ylabel('Conflicting structures');panel(ax,'e','Conflict transitions');ax._left_title.set_fontweight('normal');ax.legend(loc='upper right',frameon=False,fontsize=7)
ax=fig.add_subplot(gs[1,2:])
for col,color,label in [('robust_conflict_rate_full_support','#3E7DB6','All reconstructable'),('robust_conflict_rate_decisive_support','#E5A09B','Decisive only')]:
 ax.plot(ind.indeterminate_width_meV_per_atom,ind[col]*100,marker='o',color=color,ms=4,lw=1.7,label=label)
ax.set(xticks=[10,20,30,40,50],ylim=(0,10),yticks=[0,2,4,6,8,10]);ax.set_xlabel(r'Indeterminate width (meV atom$^{-1}$)');ax.set_ylabel('Definite conflicts (%)');panel(ax,'f','Indeterminate-zone sensitivity');ax._left_title.set_fontweight('normal');ax.legend(frameon=False,fontsize=7,loc='upper right')
assert int(ind[ind.indeterminate_width_meV_per_atom.eq(50)].robust_conflict_n.iloc[0])==512
source(phase_rows,'fig4_inventory_by_complexity.source.csv');source(decomp,'fig4_phase_inventory_decomposition.source.csv');source(ind,'fig4_phase_inventory_decisive.source.csv');save(fig,'fig4_phase_inventory')

# Figure 5: absolute counts, within-model shifts, fixed-target budgets and ranking.
fig,axs=plt.subplots(2,3,figsize=(7.2,6.0));fig.subplots_adjust(left=.10,right=.975,bottom=.145,top=.92,wspace=.50,hspace=.67)

ax=axs[0,0]
for k,model in enumerate(MODELS):
 d=hits[hits.model_name.eq(model)].set_index('coordinate_endpoint').loc[ENDS];y=np.arange(5)[::-1]+(k-1.5)*.13;v=d.expected_stable_hits.to_numpy();lo=d.bootstrap_ci_low_95.to_numpy();hi=d.bootstrap_ci_high_95.to_numpy();ax.errorbar(v,y,xerr=[v-lo,hi-v],fmt='o',color=MC[model],ms=3,lw=.75,capsize=1)
base=hits.drop_duplicates('coordinate_endpoint').set_index('coordinate_endpoint').loc[ENDS]
for y,v in zip(np.arange(5)[::-1],base.random_expected_hits):ax.vlines(v,y-.34,y+.34,color='#626A72',ls='--',lw=.85)
ax.set(yticks=np.arange(5)[::-1],yticklabels=SHORT,xlim=(300,1040),xticks=[400,700,1000],ylim=(-.5,4.5));ax.set_xlabel('Stable hits per 1,000');panel(ax,'a','Stable hits');ax.grid(axis='x',color='#E7EBEF',lw=.5)
ax=axs[0,1];mat=hits.pivot(index='model_name',columns='coordinate_endpoint',values='expected_stable_hits').loc[MODELS,ENDS].to_numpy();ax.imshow(mat,cmap='YlGnBu',vmin=500,vmax=1050,aspect='auto')
ax.set(yticks=np.arange(4),yticklabels=MODELS,xticks=np.arange(5),xticklabels=['MP','alex-\nmp-20','Alex.','MP\nshared','Alex.\nshared']);ax.set_xticklabels(['MP','alex-mp-20','Alexandria','MP shared','Alex. shared'],rotation=40,ha='right',fontsize=6);ax.tick_params(length=0,labelsize=6);panel(ax,'b','Model-by-reference counts')
for (i,j),v in np.ndenumerate(mat):ax.text(j,i,f'{v:.0f}',ha='center',va='center',fontsize=6.2,color='white' if v>850 else '#152D39')
ax=axs[0,2];gap_rows=[]
for model in MODELS:
 d=curves[curves.model_name.eq(model)].pivot(index='K',columns='coordinate_endpoint',values='expected_stable_hits').sort_index().loc[:5000]
 delta=d['official__mp_source_coordinate']-d['official__alex_pbe_source_coordinate']
 ax.plot(delta.index,delta.values,color=MC[model],lw=1.4)
 for k in [100,300,500,1000,5000]:
  ax.plot(k,delta.loc[k],marker='o',color=MC[model],ms=2.5)
 for k,value in delta.items():gap_rows.append({'model_name':model,'K':int(k),'mp_minus_alexandria_hits':float(value)})
ax.axhline(0,color='#687580',lw=.7,ls='--');ax.set(xticks=[0,1000,3000,5000],xticklabels=['0','1k','3k','5k']);ax.set_xlabel('Validation budget');ax.set_ylabel('MP minus Alexandria stable hits');panel(ax,'c','Yield gap across budgets')
source(pd.DataFrame(gap_rows),'fig5_yield_gap_by_budget.source.csv')
ax=axs[1,0];deltas=[]
for model in MODELS:
 d=hits[hits.model_name.eq(model)].set_index('coordinate_endpoint');v=d.loc[ENDS[1:],'expected_stable_hits'].to_numpy()-d.loc[ENDS[0],'expected_stable_hits'];ax.plot(np.arange(4),v,'o-',color=MC[model],ms=3)
 for e,vv in zip(ENDS[1:],v):deltas.append({'model_name':model,'endpoint':e,'delta_hits_vs_mp':vv,'K':1000})
ax.axhline(0,color='#687580',lw=.8,ls='--');ax.set(xticks=np.arange(4),xticklabels=['alex-\nmp-20','Alex.','MP\nshared','Alex.\nshared'],ylim=(-220,490),yticks=[-200,0,200,400]);ax.set_ylabel('Change in stable hits');panel(ax,'d','Change from MP');ax.grid(axis='y',color='#E7EBEF',lw=.5)
ax=axs[1,1];budget=[]
for model in MODELS:
 for endpoint in ENDS[:3]:
  d=curves[curves.model_name.eq(model)&curves.coordinate_endpoint.eq('official__'+endpoint)].sort_values('K');hit=d[d.expected_stable_hits.ge(500)].iloc[0];budget.append({'model_name':model,'endpoint':endpoint,'target_hits':500,'required_K':int(hit.K),'achieved_expected_hits':hit.expected_stable_hits})
budget=pd.DataFrame(budget)
for j,e in enumerate(ENDS[:3]):
 vals=budget[budget.endpoint.eq(e)].set_index('model_name').loc[MODELS,'required_K'].to_numpy();ax.bar(np.arange(4)+(j-1)*.23,vals,width=.21,color=EC[j],label=['MP','alex-mp-20','Alex.'][j])
ax.set(xticks=np.arange(4),xticklabels=['ALIGNN','CHGNet','M3GNet','MACE'],ylim=(0,1100),yticks=[0,500,1000]);ax.tick_params(axis='x',labelrotation=25,labelsize=6);ax.set_ylabel('Candidates validated');panel(ax,'e','Budget for 500 hits');ax.legend(frameon=False,fontsize=5.6,loc='upper center',ncol=3,columnspacing=.6,handlelength=.8);ax.grid(axis='y',color='#E7EBEF',lw=.5);ax.set_axisbelow(True)
ax=axs[1,2]
for model in MODELS:
 d=metrics[metrics.model_name.eq(model)].set_index('coordinate_endpoint').loc[ENDS];ax.plot(np.arange(5),d.normalized_ap,'o-',color=MC[model],ms=3)
ax.set(xticks=np.arange(5),xticklabels=['MP','alex-\nmp-20','Alex.','MP\nshared','Alex.\nshared'],ylim=(.15,1.03),yticks=[.2,.4,.6,.8,1]);ax.set_xticklabels(['MP','alex-mp-20','Alexandria','MP shared','Alex. shared'],rotation=35,ha='right',fontsize=6);ax.set_ylabel('Normalised average precision');panel(ax,'f','Full-ranking stability');ax.grid(axis='y',color='#E7EBEF',lw=.5)
for metric in ['auroc','ap','normalized_ap']:
 winners=metrics.loc[metrics.groupby('coordinate_endpoint')[metric].idxmax(),'model_name'];assert winners.eq('MACE-MP').all()
fig.legend(handles=[Line2D([0],[0],marker='o',color=MC[m],label=m,ms=4) for m in MODELS],loc='lower center',bbox_to_anchor=(.5,.025),ncol=4,frameon=False,columnspacing=1.8)
source(pd.DataFrame(deltas),'fig5_discovery_delta_hits.source.csv');source(budget,'fig5_fixed_target_budget.source.csv');source(metrics,'fig5_global_metrics.source.csv');source(hits,'fig5_discovery_hits.source.csv');save(fig,'fig5_discovery_consequence')
(OUT/'expanded_figure_checks.json').write_text(json.dumps({'panels':{'fig1':2,'fig2':6,'fig3':5,'fig4':6,'fig5':6,'fig6':2},'total_panels':27,'layout_checks':layout_checks,'visual_reference':'https://github.com/ChenLiu-1996/figures4papers/tree/main/figure_Brainteaser/figures','source_hashes':inputs,'checks':['D2=36802','native pair disagreements=4244/5666/3862','original/reconstructable/resolved/persistent/new/shared=5666/5661/3659/2002/2895/4897','50meV definite conflicts=512','phase comparison by complexity sums to full reconstructable counts at all four thresholds','reference-inspired repeated comparisons; no pie, scalar bar-pair, or 2x2 count matrix','MACE leads every endpoint for AUROC/AP/nAP','fixed-target budgets derived from stored tie-aware curves; no reranking'],'mace_target500_budget':budget[budget.model_name.eq('MACE-MP')].to_dict('records')},indent=2)+'\n')
print('Expanded Figures 2–5 generated; total planned panels=27; all numerical checks passed.')
