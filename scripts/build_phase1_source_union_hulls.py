import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import argparse
from pathlib import Path
from sourceaware.hulls import build_common_pool_hulls, build_source_union_hulls
from sourceaware.io import PHASE1_OUT
p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,default=PHASE1_OUT); a=p.parse_args(); build_common_pool_hulls(a.out); build_source_union_hulls(a.out)
