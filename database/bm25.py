import csv
import math
from collections import Counter
from sqlalchemy import create_engine, MetaData, Table, select, text
import os
from dotenv import load_dotenv

from config.config import get_database_engine

# ----------------------
# 0. Preprocessing Utilities
# ----------------------

STOPWORDS = {"the", "is", "at", "which", "on", "and", "a", "an", "for", "in", "to", "of", "with"}
SYNONYMS = {
    "course": ["module", "training", "class"],
    "start": ["begin", "commence"],
    "learn": ["study", "understand", "acquire"],
    "security": ["protection", "safety", "defense"],
    "data": ["information", "dataset"],
    "finance": ["financial", "economics", "banking"],
    "web": ["internet", "online"]
}


def preprocess(text):
    """Lowercase, split and remove stopwords."""
    return [word for word in text.lower().split() if word not in STOPWORDS]


def expand_query(query_terms):
    """Expand query terms with predefined synonyms."""
    expanded = []
    for term in query_terms:
        expanded.append(term)
        expanded.extend(SYNONYMS.get(term, []))
    return expanded


# ----------------------
# 1. Database Connection
# ----------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = get_database_engine(DATABASE_URL)
connection = engine.connect()
metadata = MetaData()

courses = Table('courses', metadata, autoload_with=engine)


# ----------------------
# 2. BM25 Scoring Function
# ----------------------

def bm25_score(query_terms, document_terms, avgdl, doc_len, k1=0.9, b=0.4, N=1, df={}):
    score = 0.0
    frequencies = Counter(document_terms)

    for term in query_terms:
        f = frequencies.get(term, 0)
        n = df.get(term, 0)

        if f == 0:
            # Soft penalty for missing terms
            idf = math.log((N + 0.5) / (0.5) + 1)
            score += idf * (k1 * (1 - b + b * (doc_len / avgdl)))
            continue

        idf = math.log((N - n + 0.5) / (n + 0.5) + 1)
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * (doc_len / avgdl))
        score += idf * (numerator / denominator)

    return score


# ----------------------
# 3. Perform the Search
# ----------------------

def search_courses(query_string, top_k=10):
    # Preprocess and expand query
    raw_query_terms = preprocess(query_string)
    query_terms = expand_query(raw_query_terms)

    if not query_terms:
        print("Query too vague or empty after preprocessing.")
        return

    # Step 1: Fetch candidates with flexible SQL filtering
    stmt = select(courses)
    for term in raw_query_terms:  # Use original terms to not over-fetch
        stmt = stmt.where(courses.c.embedding_input_combined.ilike(f"%{term}%"))

    result = connection.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        print("No courses found matching the query.")
        return

    # Step 2: Prepare corpus
    documents = []
    course_ids = []
    for row in rows:
        embedding_input = row['embedding_input_combined']
        if embedding_input:
            documents.append(preprocess(embedding_input))
            course_ids.append(row['course_id'])

    if not documents:
        print("No valid documents found in results.")
        return

    # Step 3: Corpus statistics
    N = len(documents)
    avgdl = sum(len(doc) for doc in documents) / N
    df = Counter()
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1

    # Step 4: BM25 scoring
    scored_courses = []
    for idx, doc in enumerate(documents):
        score = bm25_score(query_terms, doc, avgdl, len(doc), k1=0.9, b=0.4, N=N, df=df)
        scored_courses.append((rows[idx], score))

    # Step 5: Sort by score descending
    scored_courses.sort(key=lambda x: x[1], reverse=True)

    # Step 6: Output top courses
    print(f"\nTop {top_k} search results for query: '{query_string}'\n")
    for course_row, score in scored_courses[:top_k]:
        print(f"[{score:.4f}] {course_row['title']} — {course_row['course_url']}")
        print(f"    Description: {course_row['description'][:100]}...")
        print()


# ----------------------
# 4. Usage Example
# ----------------------

if __name__ == "__main__":
    with open("../tests/datasets/ir_test_queries.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        query_set = [row["query"] for row in reader]

    for user_query in query_set:
        search_courses(user_query, top_k=10)
