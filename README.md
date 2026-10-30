# Reference-Set Size and Score Aggregation in TF-IDF Cross-Language Code Retrieval

**Author:** Roman Tsoy  
**Project type:** Independent research project

## Overview

This project examines how the number of reference implementations and the aggregation of similarity scores affect a TF-IDF baseline for cross-language code retrieval.

Programs are represented with TF-IDF features over code tokens and token bigrams. For each candidate task group, query-to-reference cosine similarities are aggregated using either **maximum (Max)** or **mean (Mean)** scoring. The experiments use an AtCoder-derived Java-Python corpus and the cross-language code-to-code subset of CoREB.

The two datasets use different relevance definitions and evaluation protocols. Their absolute scores are therefore not directly comparable.

## Research questions

1. How does retrieval performance change as the number of reference implementations increases?
2. How do Max and Mean aggregation compare across reference-set sizes and datasets?
3. When filtering by test status appears to improve retrieval, does the improvement remain when the candidate group set is held fixed?

## Main findings reported in the paper

- On the fixed AtCoder evaluation cohort, query-weighted Mean Success@1 is **0.5070** with all available references, compared with **0.2046** with one reference.
- On AtCoder, Mean outperforms Max at the tested multi-reference sizes (`k = 5`, `10`, and all references). At `k = 1`, the operators are identical by definition.
- On the analyzed CoREB subset, the `k = 2` versus `k = 1` contrast is positive for the five metrics tested inferentially under both Max and Mean, using source-problem cluster-bootstrap intervals.
- The apparent benefit of filtering is smaller in the matched-candidate control, where the same candidate groups are ranked.

These findings are limited to the datasets, subsets, lexical representation, and evaluation protocols described in the paper. They do not establish that Mean is universally better than Max or that filtering always improves retrieval.

## Files in this repository

All project files are stored in the repository root. There are no nested project folders and no relative Markdown hyperlinks.

| File | Purpose |
|---|---|
| `Research_Final.pdf` | The single final research manuscript. |
| `research_workflow.ipynb` | Archival, stateful research notebook. It retains earlier XLCoST/AtCoder exploration, repeated CoREB audit cells, and later experiments. It is not a clean, single-command pipeline. Do not use “Run All”. |
| `AtCoder_Fixed_Cohort_Audit.ipynb` | Self-contained Colab/Jupyter version of the AtCoder fixed-cohort audit. |
| `AtCoder_Fixed_Cohort_Audit.py` | Standalone local Python version of the AtCoder fixed-cohort audit. |
| `AtCoder_Fixed_Cohort_Audit_Report.json` | Saved structured AtCoder audit output supplied with this release. |
| `CoREB_Reference_Count_Cluster_Bootstrap.csv` | CoREB `k = 2` minus `k = 1` cluster-bootstrap results. |
| `CoREB_Filtering_Cluster_Bootstrap.csv` | CoREB filtering and matched-candidate cluster-bootstrap results. |
| `REPRODUCIBILITY_RUN_GUIDE.md` | Dataset setup, execution guidance, dependency versions, random seeds, and bootstrap settings. |
| `RELEASE_MANIFEST.md` | Package contents and limitations. |
| `Audit_Change_Log.md` | Audit scope and packaging history. |
| `environment-reproduction.yml` | Pinned Conda environment. |
| `requirements-reproduction.txt` | Pinned pip requirements. |
| `SHA256SUMS.txt` | SHA-256 checksums for all distributed files except itself. |
| `.gitignore` | Excludes local environments, raw datasets, and temporary files from Git. |

## Datasets and provenance

The raw datasets are **not included** in this repository. Obtain them from their original sources and follow the version, checksum, attribution, and usage instructions in the run guide.

- **AtCoder / COSAL:** dataset record `https://zenodo.org/records/4002869`. The expected `AtCoder.mongo.zip` archive size is `350,063,499` bytes and its MD5 is `11e95fae502b9fffcd9771aa1d9cb01a`.
- **CoREB:** dataset repository `https://huggingface.co/datasets/hq-bench/coreb`, split `release_v2603`, pinned to immutable revision `e3f40f2609b4c52cc6d750594a87b29b370c3e06`. All three CoREB loader/audit cells use this revision rather than resolving the moving `main` branch.
- **Legacy XLCoST exploration:** two optional historical cells in the research notebook use a Google Drive share link. Its public accessibility has not been independently verified. This material is not required for the final AtCoder/CoREB experiments; skip those legacy cells if the file is inaccessible.

Do not upload raw datasets to this repository.

## Reproducibility status and limitations

The reported results are based on saved Colab notebook outputs and the supplied audit artifacts. **This repository does not claim an independent clean-room or third-party replication.** The historical Colab package freeze was not recorded. The environment files specify a documented target for future reruns; they do not reconstruct the exact historical runtime.

The original `research_workflow.ipynb` is stateful and depends on earlier cells and data files. It should not be described as a one-click reproducibility pipeline. The CoREB loaders in cells 21–23 use the same pinned revision. Some legacy XLCoST exploration relies on the optional Google Drive link noted above.

The standalone AtCoder audit script requires the original AtCoder archive, which is not bundled here. Two proposed extensions remain future work: a BM25 baseline and an equal-reference-count control for the filtering experiment.

## Getting started

Read `REPRODUCIBILITY_RUN_GUIDE.md` before executing any notebook or script. From the repository root, create the pinned Conda environment:

```bash
conda env create -f environment-reproduction.yml
conda activate code-retrieval-repro
```

Alternatively, use an existing Python 3.11 environment:

```bash
python -m pip install -r requirements-reproduction.txt
```

Do not execute the archival notebook with “Run All”. The run guide explains which experiment blocks depend on earlier state and how to check expected outputs.

## Interpretation notes

- The AtCoder descriptive table is query-weighted; its bootstrap comparisons are task-weighted. These estimate different quantities and must not be mixed.
- The CoREB group-level metrics used in the paper are custom metrics, not official document-level benchmark scores.
- The AtCoder archive checksum verifies the input archive, not the retrieval results by itself.
