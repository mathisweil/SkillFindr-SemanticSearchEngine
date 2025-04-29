from math import log2
from dotenv import load_dotenv
import os
import json
import csv

from config.config import get_database_engine
from embedding.model_loader import load_embedding_model
from embedding.retrieve_courses import semantic_search, keyword_search, bm25_search

# recall@k function
def recall(actual, predicted, k):
    act_set = set(actual)
    pred_set = set(predicted[:k])
    result = round(len(act_set & pred_set) / float(len(act_set)), 2)
    return result

actual = ["2", "4", "5", "7"]
predicted = ["1", "2", "3", "4", "5", "6", "7", "8"]
for k in range(1, 9):
    print(f"Recall@{k} = {recall(actual, predicted, k)}")


# relevant results for query #1, #2, and #3
actual_relevant = [
    [2, 4, 5, 7],
    [1, 4, 5, 7],
    [5, 8]
]

# number of queries
Q = len(actual_relevant)

# calculate the reciprocal of the first actual relevant rank
cumulative_reciprocal = 0
for i in range(Q):
    first_result = actual_relevant[i][0]
    reciprocal = 1 / first_result
    cumulative_reciprocal += reciprocal
    print(f"query #{i+1} = 1/{first_result} = {reciprocal}")

# calculate mrr
mrr = 1/Q * cumulative_reciprocal

# generate results
print("MRR =", round(mrr,2))


# initialize variables
actual = [
    [2, 4, 5, 7],
    [1, 4, 5, 7],
    [5, 8]
]
Q = len(actual)
predicted = [1, 2, 3, 4, 5, 6, 7, 8]
k = 8
ap = []

# loop through and calculate AP for each query q
for q in range(Q):
    ap_num = 0
    # loop through k values
    for x in range(k):
        # calculate precision@k
        act_set = set(actual[q])
        pred_set = set(predicted[:x+1])
        precision_at_k = len(act_set & pred_set) / (x+1)
        # calculate rel_k values
        if predicted[x] in actual[q]:
            rel_k = 1
        else:
            rel_k = 0
        # calculate numerator value for ap
        ap_num += precision_at_k * rel_k
    # now we calculate the AP value as the average of AP
    # numerator values
    ap_q = ap_num / len(actual[q])
    print(f"AP@{k}_{q+1} = {round(ap_q,2)}")
    ap.append(ap_q)

# now we take the mean of all ap values to get mAP
map_at_k = sum(ap) / Q

# generate results
print(f"mAP@{k} = {round(map_at_k, 2)}")


# initialize variables
relevance = [0, 7, 2, 4, 6, 1, 4, 3]
K = 8

dcg = 0
# loop through each item and calculate DCG
for k in range(1, K+1):
    rel_k = relevance[k-1]
    # calculate DCG
    dcg += rel_k / log2(1 + k)


# sort items in 'relevance' from most relevant to less relevant
ideal_relevance = sorted(relevance, reverse=True)

print(ideal_relevance)

idcg = 0
# as before, loop through each item and calculate *Ideal* DCG
for k in range(1, K+1):
    rel_k = ideal_relevance[k-1]
    # calculate DCG
    idcg += rel_k / log2(1 + k)


dcg = 0
idcg = 0

for k in range(1, K+1):
    # calculate rel_k values
    rel_k = relevance[k-1]
    ideal_rel_k = ideal_relevance[k-1]
    # calculate dcg and idcg
    dcg += rel_k / log2(1 + k)
    idcg += ideal_rel_k / log2(1 + k)
    # calcualte ndcg
    ndcg = dcg / idcg


if __name__ == "__main__":
    load_dotenv()
    model = load_embedding_model(os.getenv("EMBEDDING_MODEL_NAME"))
    engine = get_database_engine(os.getenv("DATABASE_URL"))

    with open(os.getenv("TEST_QUERIES_PATH"), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        query_set = [row["query"] for row in reader]

    with open(os.getenv("TEST_DATASET_PATH"), 'r', encoding='utf-8') as f:
        test_dataset = json.load(f)

    prediction_dataset_semantic = {}
    prediction_dataset_keyword = {}
    prediction_dataset_bm25 = {}

    for query in query_set:
        semantic_search_results = semantic_search(query, model, engine, threshold=0.5, limit=20)
        keyword_search_results = keyword_search(query, engine, threshold=0.0, limit=20)
        bm25_search_results = bm25_search(query, engine, limit=20)

        prediction_dataset_semantic[query] = [course["course_id"] for course in semantic_search_results]
        prediction_dataset_keyword[query] = [course["course_id"] for course in keyword_search_results]
        prediction_dataset_bm25[query] = [course["course_id"] for course in bm25_search_results]
