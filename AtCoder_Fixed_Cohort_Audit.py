import os, re, json, zipfile, hashlib, random
from pathlib import Path
from collections import defaultdict

import numpy as np
from bson import decode_file_iter
from sklearn.feature_extraction.text import TfidfVectorizer

# ============================================================
# SELF-CONTAINED ATCODER FIXED-COHORT AUDIT
# Does not depend on variables from earlier notebook cells.
# ============================================================

EXPECTED_MD5 = "11e95fae502b9fffcd9771aa1d9cb01a"
PROJECT_ROOT = Path(__file__).resolve().parent
DRIVE_ARCHIVE = Path("/content/drive/MyDrive/Research_Code_Retrieval/data/AtCoder.mongo.zip")
COLAB_ARCHIVE = Path("/content/AtCoder.mongo.zip")

# Find the archive from an explicit environment variable, the repository's data/
# folder, or the conventional Colab/Google Drive locations.
archive_candidates = []
env_archive = os.environ.get("ATCODER_ARCHIVE")
if env_archive:
    archive_candidates.append(Path(env_archive).expanduser())
archive_candidates.extend([
    PROJECT_ROOT / "data" / "AtCoder.mongo.zip",
    COLAB_ARCHIVE,
    DRIVE_ARCHIVE,
])
archive_path = next((p.resolve() for p in archive_candidates if p.is_file()), None)

# Mount Google Drive only when running in Colab and no archive was found.
if archive_path is None:
    try:
        from google.colab import drive
    except ImportError:
        drive = None
    if drive is not None:
        drive.mount("/content/drive")
        archive_path = next((p.resolve() for p in archive_candidates if p.is_file()), None)

if archive_path is None:
    raise FileNotFoundError(
        "Не найден AtCoder.mongo.zip. Укажи путь через переменную окружения "
        "ATCODER_ARCHIVE или помести архив в data/AtCoder.mongo.zip "
        "в корне репозитория. В Colab также поддерживаются /content/AtCoder.mongo.zip "
        "и стандартный путь Google Drive."
    )
archive = str(archive_path)

# Verify the archive before processing it.
h = hashlib.md5()
with open(archive, "rb") as f:
    for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
        h.update(chunk)
actual_md5 = h.hexdigest()
print("Archive:", archive)
print("Archive MD5:", actual_md5)
print("Expected MD5:", EXPECTED_MD5)
if actual_md5 != EXPECTED_MD5:
    raise ValueError("MD5 не совпал с ожидаемой контрольной суммой; эксперимент остановлен.")
with zipfile.ZipFile(archive) as zf:
    bad = zf.testzip()
    if bad is not None:
        raise ValueError(f"Повреждённый файл внутри ZIP: {bad}")
    bson_files = [n for n in zf.namelist() if n.endswith("code_store.bson")]
    if not bson_files:
        raise FileNotFoundError("В архиве не найден code_store.bson")
    bson_name = bson_files[0]

# 1. Parse unique Java/Python solutions by problem, matching the original notebook.
pattern = re.compile(r"/C(\d+)/P(\d+)(?:/|$)", re.I)
groups = defaultdict(lambda: {"java": {}, "py": {}})
record_counts = defaultdict(int)
unmapped_counts = defaultdict(int)

with zipfile.ZipFile(archive) as zf:
    with zf.open(bson_name) as f:
        for d in decode_file_iter(f):
            lang = str(d.get("language", "")).lower()
            if lang not in ("java", "py"):
                continue
            record_counts[lang] += 1
            match = pattern.search(str(d.get("sourceFile", "")))
            if not match:
                unmapped_counts[lang] += 1
                continue
            task = f"C:{int(match.group(1))}-P:{int(match.group(2))}"
            code = str(d.get("code") or "").strip()
            if code:
                # Remove exact duplicate code only within the same task/language.
                groups[task][lang].setdefault(code, code)

java_tasks_all = sorted(t for t, g in groups.items() if g["java"])
shared_tasks = sorted(t for t in java_tasks_all if groups[t]["py"])

# 2. Reconstruct queries deterministically, using the original seed 42 and <=5 Python
#    implementations per shared task.
rng = random.Random(42)
queries = []
for task in shared_tasks:
    codes = list(groups[task]["py"].values())
    rng.shuffle(codes)
    queries.extend((task, code) for code in codes[:5])

# 3. Candidate index: all unique Java implementations from identifiable tasks.
candidates = [
    (task, code)
    for task in java_tasks_all
    for code in groups[task]["java"].values()
]
candidate_tasks = np.asarray([task for task, _ in candidates])
candidate_codes = [code for _, code in candidates]
query_tasks = [task for task, _ in queries]
query_codes = [code for _, code in queries]

# 4. Build the TF-IDF matrix using the same tokenizer and settings as the original cell.
token_pattern = re.compile(
    r"[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||"
    r"\+\+|--|->|[^\s]"
)
def tokenize(code):
    return token_pattern.findall(code)

vectorizer = TfidfVectorizer(
    tokenizer=tokenize,
    token_pattern=None,
    lowercase=False,
    ngram_range=(1, 2),
    sublinear_tf=True,
)
print("Building full Java TF-IDF index...")
X = vectorizer.fit_transform(candidate_codes)
Q = vectorizer.transform(query_codes)

# 5. Fixed cohort: candidate task groups with at least 10 Java implementations.
candidate_task_array = np.asarray(candidate_tasks)
all_task_indices = {
    t: np.flatnonzero(candidate_task_array == t)
    for t in sorted(set(candidate_task_array))
}
eligible_tasks = sorted(
    t for t, ix in all_task_indices.items() if len(ix) >= 10
)
eligible_set = set(eligible_tasks)
query_indices = [i for i, (task, _) in enumerate(queries) if task in eligible_set]
fixed_query_tasks = [queries[i][0] for i in query_indices]
eval_tasks = sorted(set(fixed_query_tasks))
if not query_indices or not eval_tasks:
    raise RuntimeError("Не осталось запросов после формирования фиксированной когорты.")

candidate_indices = np.flatnonzero(np.isin(candidate_task_array, eligible_tasks))
X_fixed = X[candidate_indices, :]
candidate_tasks_fixed = candidate_task_array[candidate_indices]
Q_fixed = Q[query_indices]
local_indices = {
    t: np.flatnonzero(candidate_tasks_fixed == t)
    for t in eligible_tasks
}
task_pos = {t: i for i, t in enumerate(eligible_tasks)}

# 6. Five seeds. For each task, k=1/5/10 are nested prefixes of one shuffled list.
K_VALUES = [1, 5, 10, "all"]
SEEDS = list(range(5))
selections = {}
for seed in SEEDS:
    seed_rng = random.Random(seed)
    for task in eligible_tasks:
        order = local_indices[task].tolist()
        seed_rng.shuffle(order)
        for k in K_VALUES:
            selections[seed, task, k] = order if k == "all" else order[:k]

METRICS = ["Success@1", "Success@5", "Success@10", "MRR"]
per_query = defaultdict(lambda: defaultdict(list))
per_task = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

def ranking_metrics(task_scores, gold_task):
    gold = task_scores[task_pos[gold_task]]
    higher = int(np.sum(task_scores > gold + 1e-12))
    tied = max(1, int(np.sum(np.abs(task_scores - gold) <= 1e-12)))
    out = {}
    for k in (1, 5, 10):
        out[f"Success@{k}"] = min(max(k - higher, 0), tied) / tied
    out["MRR"] = float(np.mean([1.0 / (higher + j) for j in range(1, tied + 1)]))
    return out

print("Running fixed-cohort comparison...")
for start in range(0, len(query_indices), 32):
    sims = (Q_fixed[start:start + 32] @ X_fixed.T).toarray()
    for offset, row in enumerate(sims):
        gold_task = fixed_query_tasks[start + offset]
        for seed in SEEDS:
            for k in K_VALUES:
                for method in ("max", "mean"):
                    task_scores = np.empty(len(eligible_tasks), dtype=float)
                    for j, task in enumerate(eligible_tasks):
                        vals = row[selections[seed, task, k]]
                        task_scores[j] = np.max(vals) if method == "max" else np.mean(vals)
                    outcome = ranking_metrics(task_scores, gold_task)
                    key = (seed, k, method)
                    for metric, value in outcome.items():
                        per_query[key][metric].append(float(value))
                        per_task[key][gold_task][metric].append(float(value))

# 7. Report both query-weighted and task-weighted averages, so the manuscript wording
#    can be checked against the actual aggregation used.
report = {
    "archive": {
        "path": archive,
        "md5": actual_md5,
        "bson_member": bson_name,
        "records_seen": {"Java": int(record_counts["java"]), "Python": int(record_counts["py"])},
        "unmapped_records_excluded": {"Java": int(unmapped_counts["java"]), "Python": int(unmapped_counts["py"])},
    },
    "counts": {
        "all_java_candidate_programs": int(len(candidates)),
        "fixed_cohort_java_candidate_programs": int(X_fixed.shape[0]),
        "tfidf_features": int(X_fixed.shape[1]),
        "all_java_candidate_task_groups": int(len(java_tasks_all)),
        "fixed_cohort_candidate_task_groups": int(len(eligible_tasks)),
        "tasks_with_queries_in_fixed_cohort": int(len(eval_tasks)),
        "queries_in_fixed_cohort": int(len(query_indices)),
        "reference_seeds": SEEDS,
        "reference_counts": K_VALUES,
    },
    "results": {},
}

for k in K_VALUES:
    kkey = str(k)
    report["results"][kkey] = {}
    for method in ("max", "mean"):
        seed_query = []
        seed_task = []
        for seed in SEEDS:
            key = (seed, k, method)
            seed_query.append({m: float(np.mean(per_query[key][m])) for m in METRICS})
            seed_task.append({
                m: float(np.mean([
                    np.mean(per_task[key][task][m])
                    for task in eval_tasks
                ]))
                for m in METRICS
            })
        report["results"][kkey][method] = {
            "query_weighted_mean_across_seeds": {
                m: round(float(np.mean([s[m] for s in seed_query])), 4) for m in METRICS
            },
            "query_weighted_sd_across_seeds": {
                m: round(float(np.std([s[m] for s in seed_query])), 4) for m in METRICS
            },
            "task_weighted_mean_across_seeds": {
                m: round(float(np.mean([s[m] for s in seed_task])), 4) for m in METRICS
            },
            "task_weighted_sd_across_seeds": {
                m: round(float(np.std([s[m] for s in seed_task])), 4) for m in METRICS
            },
        }

# 8. Task-cluster bootstrap CI for task-weighted Mean - Max, 5,000 replicates, seed 20261028.
boot_rng = np.random.default_rng(20261028)
N_BOOT = 5000
for k in K_VALUES:
    kkey = str(k)
    report["results"][kkey]["task_weighted_mean_minus_max_bootstrap"] = {}
    for metric in METRICS:
        diffs = np.asarray([
            np.mean([
                np.mean(per_task[(seed, k, "mean")][task][metric])
                - np.mean(per_task[(seed, k, "max")][task][metric])
                for seed in SEEDS
            ])
            for task in eval_tasks
        ], dtype=float)
        sampled = boot_rng.choice(diffs, size=(N_BOOT, len(diffs)), replace=True).mean(axis=1)
        report["results"][kkey]["task_weighted_mean_minus_max_bootstrap"][metric] = {
            "difference": round(float(diffs.mean()), 4),
            "ci95": [round(float(np.quantile(sampled, 0.025)), 4), round(float(np.quantile(sampled, 0.975)), 4)],
            "bootstrap_replicates": N_BOOT,
            "bootstrap_seed": 20261028,
            "cluster_unit": "task",
        }

print("\n=== ATCODER FIXED-COHORT AUDIT REPORT ===")
print(json.dumps(report, indent=2, ensure_ascii=False))

# Save the report in the repository root by default; allow an explicit output override.
default_output = PROJECT_ROOT / "AtCoder_Fixed_Cohort_Audit_Report.json"
output_path = Path(os.environ.get("ATCODER_AUDIT_OUTPUT", str(default_output))).expanduser()
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print("\nSaved report:", output_path.resolve())
try:
    from google.colab import files
    files.download(str(output_path))
except Exception:
    print("Automatic download is available only in Google Colab; use the saved report path above.")
