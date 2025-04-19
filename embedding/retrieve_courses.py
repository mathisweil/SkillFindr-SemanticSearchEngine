from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from database.sql_queries import SEMANTIC_SEARCH_QUERY

model = SentenceTransformer("all-MiniLM-L6-v2")
engine: Engine = create_engine("postgresql+psycopg2://mathisweil@localhost:5432/postgres")


def semantic_search(
    query: str,
    threshold: float = 0.5,
    limit: int = 5,
    filters: dict[str, any] | None = None
) -> list[dict[str, any]]:
    """
    Perform a pgvector‐based semantic search over the `courses` table,
    optionally applying arbitrary filters supplied as a dict.

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
    # 1. Encode
    query_vector = model.encode([query])[0].tolist()
    query_vector_str = str(query_vector)

    filters = filters or {}
    clauses = []
    params: dict[str, any] = {
        "query_vector": query_vector_str,
        "threshold": threshold,
        "limit": limit
    }

    for col, val in filters.items():
        if isinstance(val, dict) and "min" in val and "max" in val:
            clauses.append(f"{col} BETWEEN :{col}_min AND :{col}_max")
            params[f"{col}_min"] = val["min"]
            params[f"{col}_max"] = val["max"]
        elif isinstance(val, (list, tuple)):
            clauses.append(f"{col} = ANY(:{col})")
            params[col] = val
        else:
            clauses.append(f"{col} = :{col}")
            params[col] = val

    extra_where = ""
    if clauses:
        # we already have one WHERE on embedding distance
        extra_where = "\n          AND " + "\n          AND ".join(clauses)

    sql = text(f"""
    WITH matches AS (
        SELECT
            course_id,
            title,
            course_url,
            description,
            embedding_vector <=> :query_vector AS distance
        FROM courses
        WHERE embedding_vector <=> :query_vector < :threshold
          {extra_where}
        ORDER BY distance
        LIMIT :limit
    )
    SELECT * FROM matches
    UNION ALL
    SELECT
        NULL AS course_id,
        'No match found within the threshold' AS title,
        NULL AS course_url,
        NULL AS description,
        NULL AS distance
    WHERE NOT EXISTS (SELECT 1 FROM matches)
    """)

    with engine.connect() as conn:
        result = conn.execute(sql, params)
        rows = result.mappings().all()

    return [dict(row) for row in rows]

if __name__ == "__main__":
    # Define your search parameters
    query = "I want to learn about Donal Trump"
    threshold = 0.5
    limit = 5

    # Optional: define any filters you require
    filters = {
        "star_rating": {"min": 0, "max": 5},
    }

    # Execute the semantic search
    results = semantic_search(
        query=query,
        threshold=threshold,
        limit=limit,
        filters=filters
    )

    # Display the results
    print("Semantic Search Results:\n")
    for i, row in enumerate(results, start=1):
        title       = row.get("title")
        course_id   = row.get("course_id")
        course_url  = row.get("course_url")
        distance    = row.get("distance")
        print(f"{i}. {title} (ID: {course_id})")
        if course_url:
            print(f"   URL: {course_url}")

