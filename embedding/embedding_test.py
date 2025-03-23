from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics import ndcg_score

def precision_at_k(results, ground_truth, k=5):
    retrieved = results[:k]
    relevant = set(ground_truth)
    hits = sum([1 for item in retrieved if item in relevant])
    return hits / k

def recall_at_k(results, ground_truth, k=5):
    relevant = set(ground_truth)
    retrieved = set(results[:k])
    hits = len(retrieved & relevant)
    return hits / len(relevant) if relevant else 0

def mrr(results, ground_truth):
    for rank, item in enumerate(results, start=1):
        if item in ground_truth:
            return 1 / rank
    return 0

for entry in eval_set:
    query = entry["query"]
    expected = entry["expected_ids"]

    results = semantic_search(query, k=10)  # List of course IDs
    print(f"Query: {query}")
    print(f"Precision@5: {precision_at_k(results, expected, k=5):.2f}")
    print(f"Recall@5: {recall_at_k(results, expected, k=5):.2f}")
    print(f"MRR: {mrr(results, expected):.3f}")
    print()
