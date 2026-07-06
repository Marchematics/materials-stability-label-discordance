import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse
from pathlib import Path
from sourceaware.metrics import compute_model_metrics
from sourceaware.io import PHASE1_OUT
p=argparse.ArgumentParser(); p.add_argument('--labels',type=Path,default=PHASE1_OUT/'labels_by_view.parquet'); p.add_argument('--out',type=Path,default=PHASE1_OUT); a=p.parse_args(); compute_model_metrics(a.labels,a.out)
