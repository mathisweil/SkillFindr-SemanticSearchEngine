from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sql_queries import SEMANTIC_SEARCH_QUERY, BM25_SEARCH_QUERY

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "Cybersecurity Fundamentals"
query_vector = model.encode([query])[0].tolist()

DATABASE_URL = "postgresql+psycopg2://mathisweil@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

query_vector_str = str(query_vector)

with engine.connect() as conn:
    semantic_results = conn.execute(
        text(SEMANTIC_SEARCH_QUERY),
        {"query_vector": query_vector_str, "threshold": 0.5, "limit": 5}
    ).fetchall()

print("Semantic Search Results:\n")
semantic_context = "\n\n".join(
    f"{row.course_url} - {row.course_id}" for row in semantic_results
)
print(semantic_context)

with engine.connect() as conn:
    bm25_results = conn.execute(
        text(BM25_SEARCH_QUERY),
        {"query": query, "limit": 5}
    ).fetchall()

print("\nBM25-style Results:\n")
for row in bm25_results:
    print(f"{row.title} - {row.course_url} (Rank: {row.rank})")
