import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
import numpy as np

# Replace with your PostgreSQL connection string
DATABASE_URL = "postgresql+psycopg2://username:password@host:port/database"
engine = create_engine(DATABASE_URL)

# Let's assume df has the following columns:
# ["course_url", "title_clean", "title_raw", "description_clean", "description_raw",
#  "tags_clean", "tags_raw", "duration", "learners_amount", "star_rating",
#  "star_num_ratings", "languages", "embedding_input_combined", "embedding_vector"]

# Ensure that the columns "tags_clean", "tags_raw", and "languages" are stored as lists.
# For the vector column, ensure that each row is a list or numpy array of the correct dimension.

# You might want to convert NumPy arrays to lists:
df["embedding_vector"] = df["embedding_vector"].apply(lambda v: v.tolist() if isinstance(v, np.ndarray) else v)

# Use df.to_sql() for non-vector columns if desired, but note that to_sql may not directly support pgvector.
# One common approach is to insert rows manually or using a bulk insert.

# Example using SQLAlchemy's connection and a manual insert:
insert_query = text("""
    INSERT INTO courses (
        course_url, title_clean, title_raw, description_clean, description_raw,
        tags_clean, tags_raw, duration, learners_amount, star_rating, star_num_ratings,
        languages, embedding_input_combined, embedding_vector
    ) VALUES (
        :course_url, :title_clean, :title_raw, :description_clean, :description_raw,
        :tags_clean, :tags_raw, :duration, :learners_amount, :star_rating, :star_num_ratings,
        :languages, :embedding_input_combined, :embedding_vector
    )
""")

# Convert Python lists (for tags, languages, and embedding_vector) to the appropriate format.
def prepare_row(row):
    return {
        "course_url": row["course_url"],
        "title_clean": row["title_clean"],
        "title_raw": row["title_raw"],
        "description_clean": row["description_clean"],
        "description_raw": row["description_raw"],
        "tags_clean": row["tags_clean"],   # psycopg2 will handle Python lists for PostgreSQL array types.
        "tags_raw": row["tags_raw"],
        "duration": row["duration"],
        "learners_amount": row["learners_amount"],
        "star_rating": row["star_rating"],
        "star_num_ratings": row["star_num_ratings"],
        "languages": row["languages"],
        "embedding_input_combined": row["embedding_input_combined"],
        # For pgvector, pass the vector as a list. You may need to cast to string depending on your driver.
        "embedding_vector": row["embedding_vector"]
    }

with engine.begin() as connection:
    for _, row in df.iterrows():
        connection.execute(insert_query, prepare_row(row))
