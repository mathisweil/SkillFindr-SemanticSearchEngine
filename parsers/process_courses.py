import os
import pandas as pd
from pathlib import Path

from dotenv import load_dotenv

from utils.io_utils import save_data, load_data
from parsers.text_cleaner import clean_title, clean_tags, convert_duration
from parsers.html_cleaner import DescriptionCleaner
from parsers.metadata_extractor import (
    extract_learner_count,
    extract_star_rating,
    extract_numeric,
)


def filter_and_index(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with a valid course_url, derive course_id, drop duplicates."""
    df = df[df["course_url"].notna()].copy()
    df["course_id"] = (
        df["course_url"]
        .astype(str)
        .str.rsplit("/", n=1)
        .str[-1]
        .where(lambda s: s.str.strip().astype(bool))
    )
    df = df[df["course_id"].notna()]
    return df.drop_duplicates(subset="course_id")


def clean_titles(df: pd.DataFrame) -> None:
    """Populate title_raw + title."""
    df["title_raw"] = df["title"]
    df["title"] = (
        df["title"]
        .where(df["title"].notna(), "")
        .astype(str)
        .apply(lambda s: clean_title(s) if s.strip() else "")
    )


def clean_descriptions(df: pd.DataFrame) -> None:
    """Populate description_raw + (description, languages)."""
    cleaner = DescriptionCleaner()
    df["description_raw"] = df["description"]
    cleaned = (
        df["description"]
        .fillna("")
        .astype(str)
        .apply(cleaner.clean)
        .tolist()
    )
    # split tuples into two columns
    df[["description", "languages"]] = pd.DataFrame(cleaned, index=df.index)


def clean_tags_and_metadata(df: pd.DataFrame) -> None:
    """Clean tags, duration, learner counts, star ratings, star counts."""
    df["tags_raw"] = df["tags"]
    df["tags"] = df["tags"].apply(lambda t: clean_tags(t) if isinstance(t, list) else [])

    df["duration"] = (
        df["duration"]
        .apply(lambda x: convert_duration(x) if pd.notna(x) else pd.NA)
        .astype("Int64")
    )
    df["learners_amount"] = (
        df["learners_amount"]
        .apply(lambda x: extract_learner_count(x) if pd.notna(x) else pd.NA)
        .astype("Int64")
    )
    df["star_rating"] = (
        df["star_rating"]
        .apply(lambda x: extract_star_rating(x) if pd.notna(x) else pd.NA)
        .astype("Float64")
    )
    df["star_num_ratings"] = (
        df["star_num_ratings"]
        .apply(lambda x: extract_numeric(x) if pd.notna(x) else pd.NA)
        .astype("Int64")
    )


def sort_and_save(df: pd.DataFrame, output_path: Path) -> None:
    """Sort the DataFrame and write to CSV + JSON."""
    out = df.sort_values(
        by=["learners_amount", "star_rating"], ascending=[False, False]
    )

    output_path.mkdir(parents=True, exist_ok=True)
    save_data(
        out,
        output_path / "processed_courses.csv",
        output_path / "processed_courses.json",
    )


def run_pipeline() -> None:
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv()

    RAW_OUTPUT_PATH = BASE_DIR / os.getenv("RAW_OUTPUT_PATH", "output/raw_data")
    df = load_data(RAW_OUTPUT_PATH)

    df = filter_and_index(df)
    clean_titles(df)
    clean_descriptions(df)
    clean_tags_and_metadata(df)

    PROCESSED_OUTPUT_PATH = BASE_DIR / os.getenv("PROCESSED_OUTPUT_PATH", "output/processed_data")
    sort_and_save(df, PROCESSED_OUTPUT_PATH)


if __name__ == "__main__":
    run_pipeline()