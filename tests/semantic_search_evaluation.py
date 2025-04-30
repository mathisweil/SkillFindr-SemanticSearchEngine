import os
import math
import json
import csv
import warnings
from sqlalchemy.exc import SAWarning

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
        # test_dataset: { query -> [ { "course_id": "2" }, … ] }

    # 4.4 Gather predictions
    prediction_semantic = {}
    prediction_keyword  = {}
    prediction_bm25     = {}

    for q in query_list:
        sem = semantic_search(q, model, engine, threshold=0.5, limit=20)
        kw  = keyword_search(q, engine, threshold=0.0, limit=20)
        bm  = bm25_search(q, engine, limit=20)

        prediction_semantic[q] = [c["course_id"] for c in sem]
        prediction_keyword[q]  = [c["course_id"] for c in kw]
        prediction_bm25[q]     = [c["course_id"] for c in bm]

    # 4.5 Evaluate all three
    K = 20
    results = {
        "Semantic": evaluate(prediction_semantic, test_dataset, K),
        "Keyword":  evaluate(prediction_keyword,  test_dataset, K),
        "BM25":     evaluate(prediction_bm25,     test_dataset, K),
    }

    # 4.6 Display
    print(f"Evaluation over {len(test_dataset)} queries @ K={K}\n")
    for name, metrics in results.items():
        print(f"--- {name} Search ---")
        for metric, val in metrics.items():
            print(f"{metric:10s}: {val}")
        print()

    # test = "advanced deep reinforcement learning techniques explained"
    #
    # print([f"course_id: {c["course_id"]}, title + description + tags: {c["embedding_input_combined"]}" for c in semantic_search(test, model, engine, threshold=0.7, limit=30)])
    # print([f"course_id: {c["course_id"]}, title + description + tags: {c["embedding_input_combined"]}" for c in keyword_search(test, engine, threshold=0.0, limit=20)])
    # print([f"course_id: {c["course_id"]}, title + description + tags: {c["embedding_input_combined"]}" for c in bm25_search(test, engine, limit=20)])
