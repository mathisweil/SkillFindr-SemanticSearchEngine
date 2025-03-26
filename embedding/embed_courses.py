from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from utils.config import load_config
from database.sql_queries import CREATE_TABLE_QUERY, INSERT_QUERY
from utils.io_utils import load_data

# -------------------------
# Global Configuration
# -------------------------
DATABASE_URL = "postgresql+psycopg2://mathisweil@localhost:5432/postgres"
MODEL_NAME = "all-MiniLM-L6-v2"  # Model outputs 384-dimensional vectors


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
    config = load_config()

    # Load and process data
    df = load_data(config['processed_output_path']).drop_duplicates(subset="course_id")

    for col in ["duration", "learners_amount", "star_num_ratings"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

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
