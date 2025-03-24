from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from utils.config import load_config

# -------------------------
# Global Configuration
# -------------------------
DATABASE_URL = "postgresql+psycopg2://mathisweil@localhost:5432/postgres"
MODEL_NAME = "all-MiniLM-L6-v2"  # Model outputs 384-dimensional vectors

CREATE_TABLE_QUERY = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
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

INSERT_QUERY = text("""
INSERT INTO courses (
    course_id, course_url, category, type, title, duration, learners_amount, star_rating, star_num_ratings,
    description, tags, title_raw, description_raw, languages, tags_raw, embedding_input_combined, embedding_vector
) VALUES (
    :course_id, :course_url, :category, :type, :title, :duration, :learners_amount, :star_rating, :star_num_ratings,
    :description, :tags, :title_raw, :description_raw, :languages, :tags_raw, :embedding_input_combined, :embedding_vector
)
ON CONFLICT (course_id)
DO UPDATE SET 
    course_url = EXCLUDED.course_url,
    category = EXCLUDED.category,
    type = EXCLUDED.type,
    title = EXCLUDED.title,
    duration = EXCLUDED.duration,
    learners_amount = EXCLUDED.learners_amount,
    star_rating = EXCLUDED.star_rating,
    star_num_ratings = EXCLUDED.star_num_ratings,
    description = EXCLUDED.description,
    tags = EXCLUDED.tags,
    title_raw = EXCLUDED.title_raw,
    description_raw = EXCLUDED.description_raw,
    languages = EXCLUDED.languages,
    tags_raw = EXCLUDED.tags_raw,
    embedding_input_combined = EXCLUDED.embedding_input_combined,
    embedding_vector = EXCLUDED.embedding_vector;
""")


def load_data() -> pd.DataFrame:
    """
    Loads all JSON files from the processed output directory into a single pandas DataFrame,
    removing duplicates based on the 'course_id' field.
    """
    config = load_config()
    processed_dir = Path(f"{config['processed_output_path']}")
    dataframes = []

    for file_path in sorted(processed_dir.glob("*.json")):
        df = pd.read_json(file_path)
        dataframes.append(df)

    if not dataframes:
        return pd.DataFrame()

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df.drop_duplicates(subset="course_id")


def build_combined_text(row: dict) -> str:
    """
    Constructs a combined text string from title, description, and tags.
    """
    title = row.get("title", "")
    description = row.get("description", "")
    tags = "; ".join(row.get("tags", []))
    if tags:
        return f"{title}. {description}. Tags: {tags}"
    return f"{title}. {description}"


def compute_embeddings(df: pd.DataFrame, model: SentenceTransformer) -> pd.DataFrame:
    """
    Computes the combined text and its corresponding embedding vector for each row.
    """
    df["embedding_input_combined"] = df.apply(build_combined_text, axis=1)
    df["embedding_vector"] = model.encode(
        df["embedding_input_combined"].tolist(), show_progress_bar=True
    ).tolist()
    return df


def setup_database(engine) -> None:
    """
    Creates the PostgreSQL table with the pgvector extension if it does not exist.
    """
    with engine.begin() as connection:
        connection.execute(text(CREATE_TABLE_QUERY))
    print("Table is ready in PostgreSQL.")


def prepare_row(row: dict) -> dict:
    """
    Prepares a dictionary for a single row to be inserted into the database.
    """
    return {
        "course_id": row["course_id"],
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


def insert_data(engine, df: pd.DataFrame) -> None:
    """
    Inserts all rows from the DataFrame into the PostgreSQL table.
    """
    # Prepare records using list comprehension for batch insertion.
    records = [prepare_row(row) for row in df.to_dict(orient="records")]
    with engine.begin() as connection:
        connection.execute(INSERT_QUERY, records)
    print("Data embedded and stored in PostgreSQL successfully!")


def main():
    # Load and process data
    df = load_data()
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print("Computing embeddings for combined input...")

    df = compute_embeddings(df, model)

    # Set up database and insert data
    engine = create_engine(DATABASE_URL)
    setup_database(engine)
    print("Inserting data into PostgreSQL...")
    insert_data(engine, df)


if __name__ == "__main__":
    main()
