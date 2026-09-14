"""Package the paper, figures and their reproducible inputs for a GitHub release."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION='2.1.2'
DEST=ROOT/'dist'/f'SourceAware-Stability-v{VERSION}'
DEST.mkdir(parents=True,exist_ok=True)
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for path in (ROOT/'manuscript').rglob('*'):
 if path.is_file() and path.suffix in {'.tex','.bib','.bst','.bbl','.pdf','.svg','.sty'}:copy(path,DEST/path.relative_to(ROOT))
for name in ['DATA_PROVENANCE.md','LICENSE','CITATION.cff','environment.yml','requirements-lock.txt']:
 copy(ROOT/name,DEST/name)
for name in ['build_publication_figures.py','run_alternative_clustering_bootstrap.py']:
 copy(ROOT/'scripts'/name,DEST/'scripts'/name)
shutil.copytree(ROOT/'outputs/publication',DEST/'outputs/publication',dirs_exist_ok=True)
primary=ROOT/'outputs/referee_revision_v3'
for rel in ['row_level_hull_distance_labels.parquet','candidate_pool_manifest.parquet','reference_phase_pool_manifest.parquet','structural_equivalence_classes.parquet','structural_equivalence_edges.parquet','structural_equivalence_metadata.json','A1_claim_to_output_map.csv','A1_claim_to_output_map.json']:
 copy(primary/rel,DEST/'outputs/referee_revision_v3'/rel)
for sub in ['evaluation','bootstrap','bootstrap_conflicts','matching_sensitivity','source_input_card','mphys_support_exclusion_audit','alternative_clustering_bootstrap']:
 for path in (primary/sub).glob('*'):
  if path.is_file() and (path.suffix in ['.csv','.json'] or path.name=='mphys_fixed_support.parquet'):
   copy(path,DEST/'outputs/referee_revision_v3'/path.relative_to(primary))
(DEST/'README.md').write_text('''# SourceAware-Stability v2.1.2

The choice of stability reference changes what crystal-discovery benchmarks count as success.

- `manuscript/main.pdf`: paper, with 62 references.
- `manuscript/supplementary_information.pdf`: Tables S1–S22 and detailed methods.
- `manuscript/figures/`: six main figures and the TOC graphic.
- `outputs/`: matched labels, model scores, evaluation tables and figure inputs.

Create the environment from `environment.yml`. Regenerate Figures 2–5 with:

```bash
python scripts/build_publication_figures.py
```

Rebuild either PDF from `manuscript/` with `latexmk -pdf main.tex` or `latexmk -pdf supplementary_information.tex`.

Alternative bootstrap summaries can be regenerated with `python scripts/run_alternative_clustering_bootstrap.py --root . --replicates 1000 --output /tmp/sourceaware-bootstrap`.

Repository and full analysis scripts: https://github.com/Marchematics/materials-stability-label-discordance
''')
files=[p for p in DEST.rglob('*') if p.is_file() and p.name!='MANIFEST.json']
manifest={'version':VERSION,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':[{'path':str(p.relative_to(DEST)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(DEST/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=DEST.parent/(DEST.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
print(archive)
