Dear Editors,

We submit **"Source-native stability-label uncertainty in crystal discovery
benchmarks"** as an Article for *npj Computational Materials*.

Machine-learning crystal discovery increasingly relies on binary DFT-derived
stability labels, yet public computational materials databases use different
workflows, correction schemes and hull references. We provide a strict
source-native audit of 43,139 Materials Project--Alexandria matched crystal
structures and show that 11.7% of binary stability labels disagree across
sources. We further show that this source-label choice changes benchmark
readouts under fixed predictions, including precision@300/500 shifts in a
CHGNet model-facing sensitivity check.

The manuscript is not a new model leaderboard and does not claim that DFT labels
are invalid. Instead, it provides a reproducible benchmark-reliability analysis
and a practical source-aware reporting recommendation for materials-discovery
benchmarks.

All derived public-safe tables, figure source data, scripts and SHA256
manifests are archived at Zenodo
(`https://doi.org/10.5281/zenodo.20392665`) and mirrored in the public GitHub
repository.

Sincerely,

Yu Chen, on behalf of all authors

Corresponding author: Yu Chen, chenyu@zua.edu.cn
