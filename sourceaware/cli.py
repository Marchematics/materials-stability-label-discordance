from __future__ import annotations
import argparse, subprocess, sys, os
from pathlib import Path
from .io import PHASE1_OUT, write_manifest
from .hulls import build_common_pool_hulls, build_source_union_hulls
from .labels import build_label_views
from .metrics import compute_model_metrics
from .cards import generate_card
from .plots import build_figure_source_data
def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('audit'); a.add_argument('--out',type=Path,default=PHASE1_OUT)
    e=sub.add_parser('evaluate'); e.add_argument('--labels',type=Path,required=True); e.add_argument('--out',type=Path,default=PHASE1_OUT)
    c=sub.add_parser('card'); c.add_argument('--labels',type=Path,required=True); c.add_argument('--metrics',type=Path,required=True); c.add_argument('--out',type=Path,required=True)
    args=p.parse_args(argv)
    if args.cmd=='audit':
        root=Path(__file__).resolve().parents[1]; env=os.environ.copy(); env['PYTHONPATH']=str(root)+os.pathsep+env.get('PYTHONPATH',''); subprocess.check_call([sys.executable,str(root/'scripts/build_phase1_denominators.py'),'--out',str(args.out)], cwd=str(root), env=env); build_common_pool_hulls(args.out); build_source_union_hulls(args.out); build_label_views(args.out); compute_model_metrics(args.out/'labels_by_view.parquet',args.out); build_figure_source_data(args.out); write_manifest(args.out, list(Path(args.out).rglob('*')), script='sourceaware.cli audit'); generate_card(args.out/'labels_by_view.parquet',args.out/'model_metrics_by_label_view.csv',args.out/'benchmark_card_main.json'); write_manifest(args.out, list(Path(args.out).rglob('*')), script='sourceaware.cli audit'); generate_card(args.out/'labels_by_view.parquet',args.out/'model_metrics_by_label_view.csv',args.out/'benchmark_card_main.json'); return 0
    if args.cmd=='evaluate': compute_model_metrics(args.labels,args.out); return 0
    if args.cmd=='card': generate_card(args.labels,args.metrics,args.out); return 0
if __name__=='__main__': raise SystemExit(main())
