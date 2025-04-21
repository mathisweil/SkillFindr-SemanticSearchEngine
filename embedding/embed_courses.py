import pandas as pd
from sentence_transformers import SentenceTransformer

from utils.text_utils import build_combined_text


def compute_embeddings(df: pd.DataFrame, model: SentenceTransformer) -> pd.DataFrame:
    """
    Computes the combined text and its corresponding embedding vector for each row.
    """
    df["embedding_input_combined"] = df.apply(build_combined_text, axis=1)
    df["embedding_vector"] = model.encode(
        df["embedding_input_combined"].tolist(), show_progress_bar=True
    ).tolist()
    return df
