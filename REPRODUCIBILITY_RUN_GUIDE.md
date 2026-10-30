# Reproduction Guide — TF-IDF Cross-Language Code Retrieval

## Repository layout

All files are in the repository root. Run commands from the directory containing `README.md`.

## Release contents

- `research_workflow.ipynb`: original stateful research notebook, including exploratory and later experiment cells. It is not a single-command pipeline.
- `AtCoder_Fixed_Cohort_Audit.ipynb`: self-contained Colab/Jupyter version of the AtCoder fixed-cohort audit.
- `AtCoder_Fixed_Cohort_Audit.py`: standalone local Python version of the AtCoder fixed-cohort audit.
- `AtCoder_Fixed_Cohort_Audit_Report.json`: saved structured AtCoder audit output supplied with this release.
- `CoREB_Reference_Count_Cluster_Bootstrap.csv` and `CoREB_Filtering_Cluster_Bootstrap.csv`: saved CoREB bootstrap outputs.
- `environment-reproduction.yml` and `requirements-reproduction.txt`: pinned dependencies for a documented future rerun. The original historical Colab package freeze was not stored, so these files do not claim to recreate the exact old runtime.
- `Audit_Change_Log.md` and `RELEASE_MANIFEST.md`: audit history and package limitations.

## Set up the environment

Run commands from the repository root:

```bash
conda env create -f environment-reproduction.yml
conda activate code-retrieval-repro
```

Alternatively, in an existing Python 3.11 environment:

```bash
python -m pip install -r requirements-reproduction.txt
```

The notebook's per-section package installation commands are pinned to the versions in the environment manifests; no cell uses floating `pip install -U` upgrades. If using Google Colab, clone the repository and install the pinned requirements before running selected cells:

```python
!git clone https://github.com/gokesss/cross-language-code-retrieval.git
%cd cross-language-code-retrieval
%pip install -r requirements-reproduction.txt
```

These dependency files specify a documented rerun target, not the historical Colab freeze. If running in Google Colab, record `python --version` and `pip freeze` before execution.

## Data sources and versions

### AtCoder / COSAL

Download `AtCoder.mongo.zip` from the COSAL dataset record `https://zenodo.org/records/4002869`. The expected exact archive size is `350,063,499` bytes and its MD5 is `11e95fae502b9fffcd9771aa1d9cb01a`. The script verifies the MD5 and ZIP integrity before processing.

The standalone script searches these locations in order:
- The path set in the `ATCODER_ARCHIVE` environment variable.
- `data/AtCoder.mongo.zip` under the repository root.
- `/content/AtCoder.mongo.zip` and the documented Google Drive location when running in Colab.

On Windows PowerShell:

```powershell
$env:ATCODER_ARCHIVE = "C:\path\to\AtCoder.mongo.zip"
python AtCoder_Fixed_Cohort_Audit.py
```

On macOS/Linux:

```bash
export ATCODER_ARCHIVE="/path/to/AtCoder.mongo.zip"
python AtCoder_Fixed_Cohort_Audit.py
```

By default, the script writes `AtCoder_Fixed_Cohort_Audit_Report.json` in the repository root. Set `ATCODER_AUDIT_OUTPUT` to use another output path. The script does not download or redistribute the raw dataset.

The notebook version works in Colab and local Jupyter. It checks `ATCODER_ARCHIVE`, `data/AtCoder.mongo.zip`, and then the standard Colab/Google Drive paths. By default it saves `AtCoder_Fixed_Cohort_Audit_Report.json` in the current working directory; in Colab it also triggers a file download. Set `ATCODER_AUDIT_OUTPUT` to override the output path.

### CoREB

Use the dataset repository `https://huggingface.co/datasets/hq-bench/coreb` at pinned revision `e3f40f2609b4c52cc6d750594a87b29b370c3e06`, split `release_v2603`. The immutable revision used by all three CoREB loader/audit blocks (cells 21, 22, and 23) is:

```text
e3f40f2609b4c52cc6d750594a87b29b370c3e06
```

All three loaders use this literal revision; they do not query the moving `main` branch at runtime. The three configurations loaded are `code_corpus`, `code2code_queries`, and `code2code_qrels`.

For the CoREB rerun:
1. Use a fresh Colab or Jupyter runtime and install the pinned dependencies above.
2. Load all three configurations at the pinned revision. Cells 21–23 are loading/audit stages and use the same revision.
3. Use the final retrieval/filtering experiment cells only after their required data variables have been loaded and checked. The notebook is stateful; it is not safe to execute every cell in sequence without reviewing its content.
4. The filtering cluster-bootstrap block is headed `COREB: CLUSTER BOOTSTRAP BY SOURCE PROBLEM`. It requires in-memory `q`, `results`, and `control` created by preceding retrieval and matched-candidate experiments. It writes `coreb_cluster_bootstrap_audit.csv` to the current working directory / configured Colab location.
5. The reference-count bootstrap block is headed `COREB: CLUSTER BOOTSTRAP FOR REFERENCE COUNT (k=2 vs k=1)`. It reconstructs the grouped retrieval experiment from loaded `corpus`, `queries`, and `qrels`, and writes `coreb_k_comparison_bootstrap.csv`.
6. Check query counts, source-problem cluster count, seeds, and output tables against the paper and supplied CSVs before interpreting a fresh run as a replication.

The saved CoREB CSVs in this repository are outputs from the supplied Colab workflow. Their presence is not evidence that a fresh independent rerun has succeeded.

### Optional legacy XLCoST exploration

The archival notebook contains optional historical XLCoST exploration cells that use a Google Drive share link. Public access to this external file could not be independently verified during packaging. These cells are not required for the final AtCoder/CoREB experiments; skip them if the file is unavailable. The raw XLCoST archive is not included in this repository.

## Exact bootstrap settings

### CoREB reference-count comparison
- Contrast: k=2 minus k=1, separately for Max and Mean.
- Random reference selection: seeds 0–9 for the one-reference condition; the per-query metric is averaged across seeds before cluster resampling.
- Bootstrap: 5,000 replicates, NumPy `default_rng`, seed `20261031`.
- Cluster: 61 unique `meta_source_problem_id` source problems; all paired query rows for each sampled source problem are retained.
- Interval: percentile bounds at quantiles 0.025 and 0.975.

### CoREB filtering and matched-candidate comparisons
- Bootstrap: 5,000 replicates for each comparison, percentile bounds at quantiles 0.025 and 0.975, NumPy `default_rng`.
- Base seed: `20261030`; comparison seeds in execution order: `20261030` (one-passed minus one-any, unrestricted), `20261031` (all-passed minus all-any, Max, unrestricted), `20261032` (same, Mean), `20261033` (passed versus all references, Max, matched candidate set), `20261034` (same, Mean).
- Pairing and cluster unit: comparison conditions are joined by query; random-reference seeds are averaged within each query; bootstrap clusters are the 61 `meta_source_problem_id` values. All paired queries for a sampled source problem are included together.
- Difference direction: first-named/condition-A minus second-named/condition-B, that is passed minus all.

### AtCoder
- Fixed-cohort reference-selection seeds: `0–4`; reference counts: `k = 1, 5, 10, all`.
- Main descriptive metrics are query-weighted.
- Reference-size contrasts: 10,000 task-level bootstrap replicates, seed `20261028`; Max-versus-Mean contrasts: 5,000 task-level bootstrap replicates, seed `20261028`.
- Do not mix query-weighted descriptive values with task-weighted bootstrap effects; they estimate different quantities.

## Verify the packaged files

From the repository root:

```bash
# macOS / Linux / Git Bash
sha256sum -c SHA256SUMS.txt
```

On Windows PowerShell:

```powershell
Get-Content SHA256SUMS.txt | ForEach-Object {
    $parts = $_ -split '\s{2}', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $parts[1]).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw "SHA-256 mismatch: $($parts[1])" }
}
```

`SHA256SUMS.txt` lists every distributed project file except itself. The ZIP archive integrity is checked separately.

## Known limitations

- The reported results are based on saved Colab notebook outputs and supplied audit artifacts; this package does not claim an independent third-party or clean-room replication.
- `research_workflow.ipynb` is a stateful research notebook with exploratory cells and dependencies on variables created earlier in the notebook; it is not a single-command executable. **Do not use “Run All”.**
- Exact historical package versions for the original Colab session were not recorded. The provided pins define a consistent future rerun environment rather than a claim about the original runtime.
- Raw datasets are not included. Download them from the original sources and follow their attribution and usage terms.
- Two proposed extensions remain future work: a BM25 baseline and an equal-reference-count control.
