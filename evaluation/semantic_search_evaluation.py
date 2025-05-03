import os
import math
import json
import csv
import warnings
import time

import matplotlib.pyplot as plt
from sqlalchemy.exc import SAWarning
from dotenv import load_dotenv

from config.config import get_database_engine
from embedding.model_loader import load_embedding_model
from embedding.retrieve_courses import (
    semantic_search,
    keyword_search,
    bm25_search,
)

warnings.filterwarnings("ignore", category=SAWarning)


def precision_at_k(actual: list[str], predicted: list[str], k: int) -> float:
    """
    Precision@k = (# of relevant items in top-k) / k
    """
    if k <= 0:
        return 0.0
    act_set = set(actual)
    topk = predicted[:k]
    return len(act_set & set(topk)) / k


def recall_at_k(actual: list[str], predicted: list[str], k: int) -> float:
    if not actual:
        return 0.0
    act_set = set(actual)
    return len(act_set & set(predicted[:k])) / len(act_set)


def reciprocal_rank(actual: list[str], predicted: list[str]) -> float:
    for i, p in enumerate(predicted, start=1):
        if p in actual:
            return 1.0 / i
    return 0.0


def average_precision(actual: list[str], predicted: list[str], k: int) -> float:
    if not actual:
        return 0.0
    act_set = set(actual)
    hits = 0
    score = 0.0
    for i, p in enumerate(predicted[:k], start=1):
        if p in act_set:
            hits += 1
            score += hits / i
    return score / len(act_set)


def ndcg_at_k(actual_items: list[dict], predicted: list[str], k: int) -> float:
    def dcg(rels: list[float]) -> float:
        return sum(r / math.log2(idx + 1) for idx, r in enumerate(rels, start=1))

    rel_map = {item["course_id"]: item.get("relevance", 0) for item in actual_items}
    preds_rels = [rel_map.get(pid, 0) for pid in predicted[:k]]
    ideal_rels = sorted(rel_map.values(), reverse=True)[:k]

    max_dcg = dcg(ideal_rels)
    return dcg(preds_rels) / max_dcg if max_dcg > 0 else 0.0


def evaluate(
    predictions: dict[str, list[str]],
    test_dataset: dict[str, list[dict]],
    k: int,
) -> dict[str, float]:
    """
    Compute average Precision@k, Recall@k, MRR, MAP@k, nDCG@k over all queries.
    """
    precisions, recs, rrs, aps, ndcgs = [], [], [], [], []
    for query, actual_items in test_dataset.items():
        actual_ids = [
            itm["course_id"]
            for itm in actual_items
            if itm.get("relevance", 1) > 0
        ]
        preds = predictions.get(query, [])
        precisions.append(precision_at_k(actual_ids, preds, k))
        recs.append(recall_at_k(actual_ids, preds, k))
        rrs.append(reciprocal_rank(actual_ids, preds))
        aps.append(average_precision(actual_ids, preds, k))
        ndcgs.append(ndcg_at_k(actual_items, preds, k))

    n = max(len(test_dataset), 1)
    return {
        f"Precision@{k}": round(sum(precisions) / n, 4),
        f"Recall@{k}":    round(sum(recs)       / n, 4),
        "MRR":            round(sum(rrs)       / n, 4),
        f"MAP@{k}":       round(sum(aps)       / n, 4),
        f"nDCG@{k}":      round(sum(ndcgs)     / n, 4),
    }


def load_queries(path: str) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return [row["query"] for row in csv.DictReader(f)]


def load_test_dataset(path: str) -> dict[str, list[dict]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def gather_predictions(
    queries: list[str],
    model,
    engine,
    limit: int = 20,
) -> tuple[
    dict[str, list[str]],
    dict[str, list[str]],
    dict[str, list[str]],
    list[float],
    list[float],
    list[float],
]:
    p_sem, p_kw, p_bm = {}, {}, {}
    t_sem, t_kw, t_bm = [], [], []

    for q in queries:
        t0 = time.perf_counter()
        sem = semantic_search(q, model, engine, threshold=0.5, limit=limit)
        t_sem.append(time.perf_counter() - t0)
        p_sem[q] = [c["course_id"] for c in sem]

        t0 = time.perf_counter()
        kw = keyword_search(q, engine, threshold=0.0, limit=limit)
        t_kw.append(time.perf_counter() - t0)
        p_kw[q] = [c["course_id"] for c in kw]

        t0 = time.perf_counter()
        bm = bm25_search(q, engine, limit=limit)
        t_bm.append(time.perf_counter() - t0)
        p_bm[q] = [c["course_id"] for c in bm]

    return p_sem, p_kw, p_bm, t_sem, t_kw, t_bm


def compute_coverage(preds: dict[str, list[str]]) -> float:
    return sum(bool(v) for v in preds.values()) / len(preds)


def compute_average_latency(times: list[float]) -> float:
    return sum(times) / len(times)


def plot_metrics(results: dict[str, dict[str, float]], K: int) -> None:
    systems = list(results.keys())
    labels  = list(results[systems[0]].keys())
    values  = {lab: [results[s][lab] for s in systems] for lab in labels}

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(systems))
    w = 0.15

    for i, lab in enumerate(labels):
        ax.bar([xi + i*w for xi in x], values[lab], width=w, label=lab)

    ax.set_xticks([xi + (len(labels)-1)*w/2 for xi in x])
    ax.set_xticklabels(systems)
    ax.set_ylabel("Score")
    ax.set_title(f"Core Metrics @ K={K}")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_metrics_vs_k(
    preds: dict[str, dict[str, list[str]]],
    test_ds: dict[str, list[dict]],
    ks: list[int],
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))

    for sys, pm in preds.items():
        recs = [evaluate(pm, test_ds, k)[f"Recall@{k}"]    for k in ks]
        precs= [evaluate(pm, test_ds, k)[f"Precision@{k}"] for k in ks]
        maps = [evaluate(pm, test_ds, k)[f"MAP@{k}"]       for k in ks]
        nds  = [evaluate(pm, test_ds, k)[f"nDCG@{k}"]      for k in ks]

        ax.plot(ks, precs, marker="x", linestyle="-.", label=f"{sys} Precision")
        ax.plot(ks, recs, marker="o", linestyle="-", label=f"{sys} Recall")
        ax.plot(ks, maps, marker="s", linestyle="--", label=f"{sys} MAP")
        ax.plot(ks, nds,  marker="^", linestyle=":", label=f"{sys} nDCG")

    ax.set_xlabel("k")
    ax.set_ylabel("Score")
    ax.set_title("Metrics vs k")
    ax.grid(linestyle="--", alpha=0.5)
    ax.legend(fontsize="small", ncol=2, loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


def plot_latency(
    avg_latency: dict[str, float],
) -> None:
    systems = list(avg_latency.keys())
    avg_ms  = [avg_latency[s]*1000 for s in systems]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(systems, avg_ms, width=0.6)
    ax.set_ylabel("Average Latency (ms/query)")
    ax.set_title("Average Inference Time")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    load_dotenv()
    model  = load_embedding_model(os.getenv("EMBEDDING_MODEL_NAME"))
    engine = get_database_engine(os.getenv("DATABASE_URL"))

    queries       = load_queries(os.getenv("TEST_QUERIES_PATH"))
    test_dataset  = load_test_dataset(os.getenv("TEST_DATASET_PATH"))
    p_sem, p_kw, p_bm, t_sem, t_kw, t_bm = gather_predictions(queries, model, engine)

    K = 20
    results = {
        "Semantic": evaluate(p_sem, test_dataset, K),
        "Keyword":  evaluate(p_kw,  test_dataset, K),
        "BM25":     evaluate(p_bm,  test_dataset, K),
    }

    coverage = {
        "Semantic": compute_coverage(p_sem),
        "Keyword":  compute_coverage(p_kw),
        "BM25":     compute_coverage(p_bm),
    }
    avg_latency = {
        "Semantic": compute_average_latency(t_sem),
        "Keyword":  compute_average_latency(t_kw),
        "BM25":     compute_average_latency(t_bm),
    }

    print(f"Evaluation over {len(queries)} queries @ K={K}\n")
    for sys, metrics in results.items():
        print(f"--- {sys} Search ---")
        for metric, val in metrics.items():
            print(f"{metric:14s}: {val}")
        print(f"{'Coverage':14s}: {coverage[sys]*100:.2f}%")
        print(f"{'Latency':14s}: {avg_latency[sys]*1000:.1f} ms/query\n")

    plot_metrics(results, K)
    plot_metrics_vs_k(
        {"Semantic": p_sem, "Keyword": p_kw, "BM25": p_bm},
        test_dataset,
        ks=[1, 5, 10, K],
    )
    plot_latency(
        avg_latency,
    )


if __name__ == "__main__":
    main()
