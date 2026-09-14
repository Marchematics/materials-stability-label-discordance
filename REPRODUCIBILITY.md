# Reproduce the paper and figures

## Environment

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
```

The Python alternative is:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

## Figures and evaluation tests

```bash
bash run_all.sh
```

The figure generator reads `outputs/publication/figure_source_tables/` and `outputs/referee_revision_v3/`, and writes Figures 2–5 to `manuscript/figures/`. Figure 1's full cumulative curves and Figure 6's candidate summaries are included in the source tables. PDF and SVG figures are tracked alongside the paper; the generator also exports PNG and TIFF.

Run the checks separately with:

```bash
pytest -q tests/test_referee_revision_v3.py tests/test_tie_aware_ranking.py
```

## Manuscript

With TeX Live and latexmk installed:

```bash
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_information.tex
```

The main paper cites all 62 bibliography entries. The Supplementary Information contains Tables S1–S22 and detailed methods.

## Alternative bootstrap units

The completed summaries are in `outputs/referee_revision_v3/alternative_clustering_bootstrap/`. To regenerate them from the matched labels and fixed model scores:

```bash
python scripts/run_alternative_clustering_bootstrap.py \
  --root . --replicates 1000 --seed 20260826 \
  --output /tmp/sourceaware-bootstrap
```

## Analysis inputs

The primary evaluation uses 36,650 compounds with complete model scores and stability definitions. The three-source label comparison uses 36,802 matched structures. MP and Alexandria shared-inventory calculations retain each source's formation-energy convention.

Source acquisition and structural matching are described in `DATA_PROVENANCE.md`. The scripts in `scripts/` implement matching, hull construction, score calculation, threshold scans and bootstrap summaries. Earlier model-evaluation tables remain in their versioned output directories; `CHANGELOG.md` identifies the corresponding releases.
