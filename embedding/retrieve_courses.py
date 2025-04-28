from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.sql_queries import BM25_SEARCH_QUERY


def semantic_search(
    query: str,
    model: SentenceTransformer,
    engine: Engine,
    threshold: float = 0.4,
    limit: int = 5,
    filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """
    Perform a pgvector‐based semantic search over the `courses` table,
    optionally applying arbitrary filters supplied as a dict.

    :param engine:
    :param model:
    :param query:     The natural‐language search string.
    :param threshold: Maximum allowed vector distance.
    :param limit:     Maximum number of results to return.
    :param filters:   Dict of extra constraints, e.g.
                       {'level': 'beginner',
                        'category': ['math','cs'],
                        'duration': {'min':30, 'max':120}}
    :return:          List of row‐dicts with keys
                      course_id, title, course_url, description, distance.
    """
    query_vector = model.encode([query])[0].tolist()
    query_vector_str = str(query_vector)

    filters = filters or {}
    clauses = []
    params: dict[str, Any] = {
        "query_vector": query_vector_str,
        "threshold": threshold,
        "limit": limit
    }

    for col, val in filters.items():
        if isinstance(val, dict):
            if "min" in val and val["min"] is not None:
                clauses.append(f"{col} >= :{col}_min")
                params[f"{col}_min"] = val["min"]
            if "max" in val and val["max"] is not None:
                clauses.append(f"{col} <= :{col}_max")
                params[f"{col}_max"] = val["max"]
        elif isinstance(val, (list, tuple)):
            clauses.append(f"{col} = ANY(:{col})")
            params[col] = val
        else:
            clauses.append(f"{col} = :{col}")
            params[col] = val

    extra_where = ""
    if clauses:
        extra_where = "\n          AND " + "\n          AND ".join(clauses)

    sql = text(f"""
    WITH matches AS (
        SELECT
            course_id,
            course_url,
            title,
            description,
            embedding_vector <=> :query_vector AS distance
        FROM courses
        WHERE embedding_vector <=> :query_vector < :threshold
          {extra_where}
        ORDER BY distance
        LIMIT :limit
    )
    SELECT * FROM matches
    """)

    with engine.connect() as conn:
        result = conn.execute(sql, params)
        rows = result.mappings().all()

    return [dict(row) for row in rows]

def keyword_search(query: str, engine: Engine, threshold: float = 0.1, limit: int = 5) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        bm25_results = conn.execute(
            BM25_SEARCH_QUERY,
            {"query_text": query, "threshold": threshold, "limit": limit}
        )
        rows = bm25_results.mappings().all()

    return [dict(row) for row in rows]
