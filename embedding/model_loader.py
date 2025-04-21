from sentence_transformers import SentenceTransformer

def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Loads and returns a sentence embedding model.

    Args:
        model_name (str): The name or path of the pre-trained embedding model.

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    model = SentenceTransformer(model_name)
    return model