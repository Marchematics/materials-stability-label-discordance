import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse, jsonschema, json
from pathlib import Path
from sourceaware.cards import generate_card, SCHEMA
from sourceaware.io import PHASE1_OUT
p=argparse.ArgumentParser(); p.add_argument('--labels',type=Path,default=PHASE1_OUT/'labels_by_view.parquet'); p.add_argument('--metrics',type=Path,default=PHASE1_OUT/'model_metrics_by_label_view.csv'); p.add_argument('--out',type=Path,default=PHASE1_OUT/'benchmark_card_main.json'); p.add_argument('--check',action='store_true'); a=p.parse_args(); card=json.loads(a.out.read_text()) if a.check and a.out.exists() else generate_card(a.labels,a.metrics,a.out); jsonschema.validate(card,SCHEMA)
