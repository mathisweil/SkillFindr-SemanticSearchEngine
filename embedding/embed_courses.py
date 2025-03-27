import pandas as pd
from sentence_transformers import SentenceTransformer


# -------------------------
# Global Configuration
# -------------------------
MODEL_NAME = "all-MiniLM-L6-v2"

# -------------------------
# Load Embedding Model
# -------------------------
model = SentenceTransformer(MODEL_NAME)

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


def compute_embeddings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the combined text and its corresponding embedding vector for each row.
    """
    df["embedding_input_combined"] = df.apply(build_combined_text, axis=1)
    df["embedding_vector"] = model.encode(
        df["embedding_input_combined"].tolist(), show_progress_bar=True
    ).tolist()
    return df
