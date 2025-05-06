import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

from config.config import get_database_engine
from models.course import Course
from utils.io_utils import load_data
from embedding.model_loader import load_embedding_model
from embedding.embed_courses import compute_embeddings


def setup_database(engine):
    """
    Ensures the pgvector extension is present and creates all tables defined by SQLModel models.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    SQLModel.metadata.create_all(engine)
    print("✅ Database schema is ready.")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops duplicates and casts numeric columns.
    """
    df = df.drop_duplicates(subset="course_id")
    for col in ("duration", "learners_amount", "star_num_ratings"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def insert_data(df: pd.DataFrame, engine) -> None:
    """
    Converts each DataFrame row into a Course instance and persists via SQLModel session.
    """
    records = df.to_dict(orient="records")
    courses = [Course(**r) for r in records]
    with Session(engine) as session:
        session.add_all(courses)
        session.commit()
    print("✅ Embedded course data stored successfully.")


def setup_engine_and_model(database_url: str, embedding_model_name: str = None) -> tuple:
    """
    Initializes the SQLModel engine and the embedding model.
    """
    engine = get_database_engine(database_url)
    model = load_embedding_model(embedding_model_name)
    return engine, model


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    model_name = os.getenv("EMBEDDING_MODEL_NAME")

    engine, model = setup_engine_and_model(database_url, model_name)

    BASE_DIR = Path(__file__).resolve().parent.parent
    processed_path = BASE_DIR / os.getenv("PROCESSED_OUTPUT_PATH", "output/processed_data")
    df = load_data(processed_path)
    df = preprocess_dataframe(df)

    print("📊 Computing embeddings for combined input...")
    df = compute_embeddings(df, model)

    setup_database(engine)
    print("🛢️ Inserting data into PostgreSQL...")
    insert_data(df, engine)


if __name__ == "__main__":
    main()
