from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy import create_engine, text

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "I want to learn more about artificial intelligence."
query_vector = model.encode([query])[0].tolist()

DATABASE_URL = "postgresql+psycopg2://mathisweil@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

# Convert vector to Postgres format
query_vector_str = str(query_vector)  # e.g. '[0.12, 0.98, ...]'

search_sql = text("""
SELECT
    course_id,
    title,
    course_url,
    description,
    embedding_vector <=> :query_vector AS distance
FROM courses
ORDER BY embedding_vector <=> :query_vector
LIMIT 5
""")

with engine.connect() as conn:
    results = conn.execute(search_sql, {"query_vector": query_vector_str}).fetchall()

context = "\n\n".join([
    f"{row.title} — {row.description} — {row.course_id}" for row in results
])

print(context)
