from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy import create_engine, text

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "Cybersecurity Fundamentals"
query_vector = model.encode([query])[0].tolist()

DATABASE_URL = "postgresql+psycopg2://mathisweil@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

# Convert vector to Postgres format
query_vector_str = str(query_vector)  # e.g. '[0.12, 0.98, ...]'

# search_sql = text("""
# SELECT
#     course_id,
#     title,
#     course_url,
#     description,
#     embedding_vector <=> :query_vector AS distance
# FROM courses
# ORDER BY embedding_vector <=> :query_vector
# LIMIT 5
# """)

search_sql = text("""
WITH matches AS (
    SELECT
        course_id,
        title,
        course_url,
        description,
        embedding_vector <=> :query_vector AS distance
    FROM courses
    WHERE embedding_vector <=> :query_vector < :threshold
    ORDER BY distance
    LIMIT 5
)
SELECT * FROM matches
UNION ALL
SELECT
    NULL AS course_id,
    'No course found within the threshold' AS title,
    NULL AS course_url,
    NULL AS description,
    NULL AS distance
WHERE NOT EXISTS (SELECT 1 FROM matches)
""")

with engine.connect() as conn:
    results = conn.execute(search_sql, {"query_vector": query_vector_str, "threshold": 0.5}).fetchall()

context = "\n\n".join([
    f"{row.course_url} - {row.course_id}" for row in results
])

print(context)


bm25_sql = text("""
SELECT
    course_id,
    title,
    course_url,
    description,
    ts_rank_cd(embedding_input_combined, plainto_tsquery(:query)) AS rank
FROM courses
WHERE embedding_input_combined @@ plainto_tsquery(:query)
ORDER BY rank DESC
LIMIT 5;
""")

with engine.connect() as conn:
    results = conn.execute(bm25_sql, {"query": query}).fetchall()

print("\nBM25-style results:")
for row in results:
    print(f"{row.title} - {row.course_url} (Rank: {row.rank})")
