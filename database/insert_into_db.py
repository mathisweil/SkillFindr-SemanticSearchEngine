import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.engine import Engine

from utils.config import load_config, get_database_engine
from database.sql_queries import CREATE_TABLE_QUERY, INSERT_QUERY
from utils.io_utils import load_data
from embedding.model_loader import load_embedding_model
from embedding.embed_courses import compute_embeddings


def setup_database(engine: Engine, create_table_query: str) -> None:
    """
    Creates the PostgreSQL table with the pgvector extension if it does not exist.

    Args:
        engine: SQLAlchemy Engine instance.
        create_table_query: SQL query string for creating the table.
    """
    with engine.begin() as connection:
        connection.execute(text(create_table_query))
    print("✅ PostgreSQL table is ready.")


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


def insert_data(df: pd.DataFrame, engine: Engine, insert_query: str) -> None:
    """
    Inserts all rows from the DataFrame into the PostgreSQL table.

    Args:
        df: DataFrame containing prepared data.
        engine: SQLAlchemy Engine instance.
        insert_query: SQLAlchemy text or query string for insertion.
    """
    records = [prepare_row(record) for record in df.to_dict(orient="records")]
    with engine.begin() as connection:
        connection.execute(insert_query, records)
    print("✅ Data embedded and stored in PostgreSQL successfully!")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops duplicates and converts specific columns to integer type.
    """
    df = df.drop_duplicates(subset="course_id")
    for col in ["duration", "learners_amount", "star_num_ratings"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def setup_engine_and_model() -> tuple[Engine, SentenceTransformer]:
    """
    Initializes and returns the database engine and embedding model.
    """
    engine = get_database_engine()
    model = load_embedding_model()
    return engine, model


def main():
    """
    Entry point for the semantic indexing pipeline.
    """
    config = load_config()
    engine, model = setup_engine_and_model()

    df = load_data(config['processed_output_path'])
    df = preprocess_dataframe(df)

    print("📊 Computing embeddings for combined input...")
    df = compute_embeddings(df, model)

    setup_database(engine, CREATE_TABLE_QUERY)
    print("🛢️ Inserting data into PostgreSQL...")
    insert_data(df, engine, INSERT_QUERY)


if __name__ == "__main__":
    main()