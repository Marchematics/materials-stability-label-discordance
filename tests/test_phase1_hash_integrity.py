from pathlib import Path
import json, re, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/phase1_v2'
def test_phase1_manifest_hashes_and_fingerprints():
    man=json.loads((OUT/'manifest_phase1_v2.json').read_text())
    assert man['file_count']>0
    for rec in man['files']:
        assert {'path','sha256','rows','columns','generating_script'}.issubset(rec)
        assert re.fullmatch(r'[0-9a-f]{64}', rec['sha256'])
    fp=pd.read_parquet(OUT/'structure_fingerprints.parquet')
    assert fp.structure_hash.str.fullmatch(r'[0-9a-f]{64}').all()
    assert not fp.is_geometry_hash.astype(bool).any()
