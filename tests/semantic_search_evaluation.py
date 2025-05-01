import os
import math
import json
import csv
import warnings
import time
from sqlalchemy.exc import SAWarning
import matplotlib.pyplot as plt

# 1. Silence the SAWarning about unrecognized 'vector' column types
warnings.filterwarnings("ignore", category=SAWarning)

from dotenv import load_dotenv

from config.config import get_database_engine
from embedding.model_loader import load_embedding_model
from embedding.retrieve_courses import semantic_search, keyword_search, bm25_search

# ----------------------
# 2. Metric Functions
# ----------------------
def recall_at_k(actual: list, predicted: list, k: int) -> float:
    if not actual:
        return 0.0
    act_set = set(actual)
    pred_set = set(predicted[:k])
    return len(act_set & pred_set) / len(act_set)

def reciprocal_rank(actual: list, predicted: list) -> float:
    for idx, p in enumerate(predicted, start=1):
        if p in actual:
            return 1.0 / idx
    return 0.0

def average_precision(actual: list, predicted: list, k: int) -> float:
    if not actual:
        return 0.0
    act_set = set(actual)
    score = 0.0
    hits = 0
    for i, p in enumerate(predicted[:k], start=1):
        if p in act_set:
            hits += 1
            score += hits / i
    return score / len(act_set)

def ndcg_at_k(actual_items: list, predicted: list, k: int) -> float:
    def dcg(scores):
        return sum(rel / math.log2(idx + 1) for idx, rel in enumerate(scores, start=1))

    # Build a lookup: course_id -> graded relevance
    rel_map = {
        item["course_id"]: item.get("relevance", 0)
        for item in actual_items
    }

    # Graded relevance for each predicted item
    rels       = [rel_map.get(p, 0) for p in predicted[:k]]
    ideal_rels = sorted(rel_map.values(), reverse=True)[:k]

    idcg = dcg(ideal_rels)
    return (dcg(rels) / idcg) if idcg > 0 else 0.0

# ----------------------
# 3. Evaluation Harness
# ----------------------
def evaluate(predictions: dict, test_dataset: dict, k: int = 10) -> dict:
    """
    predictions: { query -> [predicted_course_id, ...] }
    test_dataset: { query -> [ { "course_id": ... }, ... ] }
    Returns aggregate Recall@k, MRR, MAP@k, nDCG@k.
    """
    recs, rrs, aps, ndcgs = [], [], [], []

    for query, actual_items in test_dataset.items():
        # unwrap any dicts in the ground truth to simple IDs
        actual_ids = [
            item["course_id"]
            for item in actual_items
            if isinstance(item, dict) and item.get("relevance", 1) > 0
        ]
        predicted_ids = predictions.get(query, [])

        recs.append(   recall_at_k(actual_ids, predicted_ids, k)   )
        rrs.append(    reciprocal_rank(actual_ids, predicted_ids)  )
        aps.append(    average_precision(actual_ids, predicted_ids, k) )
        ndcgs.append(ndcg_at_k(actual_items, predicted_ids, k))

    Q = len(test_dataset)
    return {
        f"Recall@{k}": round(sum(recs)  / Q, 4),
        "MRR":          round(sum(rrs)  / Q, 4),
        f"MAP@{k}":     round(sum(aps)  / Q, 4),
        f"nDCG@{k}":    round(sum(ndcgs)/ Q, 4),
    }

# ----------------------
# 4. Main
# ----------------------
if __name__ == "__main__":
    load_dotenv()

    # 4.1 Load models & DB
    model  = load_embedding_model(os.getenv("EMBEDDING_MODEL_NAME"))
    engine = get_database_engine(os.getenv("DATABASE_URL"))

    # 4.2 Load queries (keep order)
    with open(os.getenv("TEST_QUERIES_PATH"), newline='', encoding='utf-8') as f:
        reader     = csv.DictReader(f)
        query_list = [row["query"] for row in reader]

    # 4.3 Load ground-truth
    with open(os.getenv("TEST_DATASET_PATH"), 'r', encoding='utf-8') as f:
        test_dataset: dict = json.load(f)

    # 4.4 Gather predictions
    prediction_semantic = {}
    prediction_keyword  = {}
    prediction_bm25     = {}

    times_semantic = []
    times_keyword = []
    times_bm25 = []

    for q in query_list:
        # semantic_search
        t0 = time.perf_counter()
        sem = semantic_search(q, model, engine, threshold=0.5, limit=20)
        t1 = time.perf_counter()
        times_semantic.append(t1 - t0)
        prediction_semantic[q] = [c["course_id"] for c in sem]

        # keyword_search
        t0 = time.perf_counter()
        kw = keyword_search(q, engine, threshold=0.0, limit=20)
        t1 = time.perf_counter()
        times_keyword.append(t1 - t0)
        prediction_keyword[q] = [c["course_id"] for c in kw]

        # bm25_search
        t0 = time.perf_counter()
        bm = bm25_search(q, engine, limit=20)
        t1 = time.perf_counter()
        times_bm25.append(t1 - t0)
        prediction_bm25[q] = [c["course_id"] for c in bm]

        # Compute coverage rates
        total_q = len(query_list)
        coverage = {
            "Semantic": sum(1 for preds in prediction_semantic.values() if preds) / total_q,
            "Keyword": sum(1 for preds in prediction_keyword.values() if preds) / total_q,
            "BM25": sum(1 for preds in prediction_bm25.values() if preds) / total_q,
        }

        # Compute average response times (in seconds)
        avg_latency = {
            "Semantic": sum(times_semantic) / total_q,
            "Keyword": sum(times_keyword) / total_q,
            "BM25": sum(times_bm25) / total_q,
        }

    # 4.5 Evaluate all three
    K = 20
    results = {
        "Semantic": evaluate(prediction_semantic, test_dataset, K),
        "Keyword":  evaluate(prediction_keyword,  test_dataset, K),
        "BM25":     evaluate(prediction_bm25,     test_dataset, K),
    }

    # 4.6 Display
    print(f"Evaluation over {total_q} queries @ K={K}\n")
    for name, metrics in results.items():
        print(f"--- {name} Search ---")
        # original metrics
        for metric, val in metrics.items():
            print(f"{metric:10s}: {val}")
        # new coverage & latency
        cov_pct = coverage[name] * 100
        lat_ms = avg_latency[name] * 1000
        print(f"{'Coverage':10s}: {cov_pct:.2f}%")  # e.g. 95.00%
        print(f"{'Latency':10s}: {lat_ms:.1f} ms/query")  # e.g. 12.3 ms
        print()

        # ----------------------
        # 5. Plotting
        # ----------------------
        # Prepare data
        systems = list(results.keys())  # ['Semantic', 'Keyword', 'BM25']
        metrics_labels = list(results['Semantic'].keys())  # ['Recall@20','MRR','MAP@20','nDCG@20']
        metric_values = {
            label: [results[sys][label] for sys in systems]
            for label in metrics_labels
        }

        # 5.1 Grouped bar chart of core metrics @ K
        fig, ax = plt.subplots(figsize=(8, 5))
        x = range(len(systems))
        width = 0.2

        for i, label in enumerate(metrics_labels):
            ax.bar([p + i * width for p in x],
                   metric_values[label],
                   width=width,
                   label=label)

        ax.set_xticks([p + (len(metrics_labels) - 1) * width / 2 for p in x])
        ax.set_xticklabels(systems)
        ax.set_ylabel('Score')
        ax.set_title(f'Core Metrics @ K={K}')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

        # 5.2 Line plots: Recall, MAP, nDCG vs k
        ks = [1, 5, 10, 20]
        fig, ax = plt.subplots(figsize=(8, 5))

        for sys in systems:
            rec = [evaluate(
                prediction_semantic if sys == 'Semantic' else
                prediction_keyword if sys == 'Keyword' else
                prediction_bm25,
                test_dataset, k)[f"Recall@{k}"]
                   for k in ks]
            mp = [evaluate(
                prediction_semantic if sys == 'Semantic' else
                prediction_keyword if sys == 'Keyword' else
                prediction_bm25,
                test_dataset, k)[f"MAP@{k}"]
                  for k in ks]
            nd = [evaluate(
                prediction_semantic if sys == 'Semantic' else
                prediction_keyword if sys == 'Keyword' else
                prediction_bm25,
                test_dataset, k)[f"nDCG@{k}"]
                  for k in ks]

            ax.plot(ks, rec, marker='o', linestyle='-', label=f'{sys} Recall')
            ax.plot(ks, mp, marker='s', linestyle='--', label=f'{sys} MAP')
            ax.plot(ks, nd, marker='^', linestyle=':', label=f'{sys} nDCG')

        ax.set_xlabel('k')
        ax.set_ylabel('Score')
        ax.set_title('Metrics vs k')
        ax.legend(fontsize='small', ncol=2, loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()
