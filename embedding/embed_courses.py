import json
import pandas as pd
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import numpy as np

# -------------------------
# Configuration
# -------------------------
# Update with your PostgreSQL connection details.
DATABASE_URL = "postgresql+psycopg2://username:password@host:port/dbname"

# The JSON file containing your courses data.
JSON_FILE = "courses.json"

# Embedding model: Adjust model name if needed.
MODEL_NAME = "all-MiniLM-L6-v2"  # This model outputs 384-dimensional vectors

# -------------------------
# Load Data
# -------------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# -------------------------
# Compute Embeddings
# -------------------------
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Computing embeddings for combined input...")
# Here we embed the combined cleaned text.
df["embedding_vector"] = model.encode(
    df["embedding_input_combined"].tolist(),
    show_progress_bar=True
).tolist()

# -------------------------
# Set Up PostgreSQL Table (with pgvector)
# -------------------------
engine = create_engine(DATABASE_URL)

# Adjust the VECTOR dimension to match your model's output (384 for all-MiniLM-L6-v2)
create_table_query = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_url TEXT,
    category TEXT,
    type TEXT,
    title TEXT,
    duration REAL,
    learners_amount INTEGER,
    star_rating REAL,
    star_num_ratings INTEGER,
    description TEXT,
    tags TEXT[],
    title_raw TEXT,
    description_raw TEXT,
    languages TEXT[],
    tags_raw TEXT[],
    embedding_input_combined TEXT,
    embedding_vector VECTOR(384)
);
"""

with engine.begin() as connection:
    connection.execute(text(create_table_query))
print("Table is ready in PostgreSQL.")

# -------------------------
# Insert Data into PostgreSQL
# -------------------------
insert_query = text("""
INSERT INTO courses (
    course_url, category, type, title, duration, learners_amount, star_rating, star_num_ratings,
    description, tags, title_raw, description_raw, languages, tags_raw, embedding_input_combined, embedding_vector
) VALUES (
    :course_url, :category, :type, :title, :duration, :learners_amount, :star_rating, :star_num_ratings,
    :description, :tags, :title_raw, :description_raw, :languages, :tags_raw, :embedding_input_combined, :embedding_vector
)
""")

def prepare_row(row):
    # Ensure that Python lists are passed as is (psycopg2 handles them for PostgreSQL arrays)
    return {
        "course_url": row["course_url"],
        "category": row["category"],
        "type": row["type"],
        "title": row["title"],
        "duration": row["duration"],
        "learners_amount": row["learners_amount"],
        "star_rating": row["star_rating"],
        "star_num_ratings": row["star_num_ratings"],
        "description": row["description"],
        "tags": row["tags"],
        "title_raw": row["title_raw"],
        "description_raw": row["description_raw"],
        "languages": row["languages"],
        "tags_raw": row["tags_raw"],
        "embedding_input_combined": row["embedding_input_combined"],
        "embedding_vector": row["embedding_vector"]
    }

print("Inserting data into PostgreSQL...")
with engine.begin() as connection:
    for _, row in df.iterrows():
        connection.execute(insert_query, prepare_row(row))

print("Data embedded and stored in PostgreSQL successfully!")
