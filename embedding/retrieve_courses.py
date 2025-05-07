from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy.engine import Engine
from pgvector.sqlalchemy import Vector

from database.sql_queries import TF_IDF_SEARCH_QUERY
from database.bm25 import search_courses_bm25
from models.course import Course
from models.filters import Filters
from sqlalchemy import text, bindparam, Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

def semantic_search(
    query: str,
    model: SentenceTransformer,
    engine: Engine,
    threshold: float = 0.4,
    limit: int = 5,
    filters: Filters | None = None
) -> list[Course]:
    """
    Perform a pgvector‐based semantic search over the `courses` table,
    optionally applying column filters. Falls back to BM25 if no vector
    results are found.

    :param query:     The natural‐language search string (must not be empty).
    :param model:     SentenceTransformer used to embed the query.
    :param engine:    SQLAlchemy Engine for DB connection.
    :param threshold: Maximum allowed vector distance (>= 0).
    :param limit:     Maximum number of results to return (> 0).
    :param filters:   Optional Filters model with RangeFilter and list fields.
    :return:          list of `Course` instances, each with a `.distance` attr.
    """
    filters = filters or Filters()

    embedding: list[float] = model.encode([query])[0].tolist()

    params: dict[str, Any] = {
        'query_vector': embedding,
        'threshold': threshold,
        'limit': limit,
    }
    where_clauses: list[str] = [
        "embedding_vector <=> CAST(:query_vector AS vector) < :threshold"
    ]

    for col_name, rf in (
        ('star_rating', filters.star_rating),
        ('learners_amount', filters.learners_amount),
        ('duration', filters.duration),
    ):
        if rf:
            if rf.min is not None:
                where_clauses.append(f"{col_name} >= :{col_name}_min")
                params[f"{col_name}_min"] = rf.min
            if rf.max is not None:
                where_clauses.append(f"{col_name} <= :{col_name}_max")
                params[f"{col_name}_max"] = rf.max

    if filters.category:
        where_clauses.append("category = ANY(:category)")
        params["category"] = filters.category

    where_sql = "\n    AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            course_id,
            course_url,
            title,
            description,
            star_rating,
            star_num_ratings,
            learners_amount,
            duration,
            embedding_input_combined,
            embedding_vector <=> CAST(:query_vector AS vector) AS distance
        FROM courses
        WHERE
            {where_sql}
        ORDER BY distance
        LIMIT :limit
    """).bindparams(
        bindparam('query_vector',
                  type_=Vector(model.get_sentence_embedding_dimension())),
        bindparam('threshold', type_=Float),
        bindparam('limit', type_=Integer),
        *[
            bindparam(f"{col}_min", type_=Float)
            for col, rf in (
                ('star_rating', filters.star_rating),
                ('learners_amount', filters.learners_amount),
                ('duration', filters.duration),
            ) if rf and rf.min is not None
        ],
        *[
            bindparam(f"{col}_max", type_=Float)
            for col, rf in (
                ('star_rating', filters.star_rating),
                ('learners_amount', filters.learners_amount),
                ('duration', filters.duration),
            ) if rf and rf.max is not None
        ],
        *([
              bindparam('category', type_=ARRAY(String))
          ] if filters.category else [])
    )

    with Session(engine) as session:
        result = session.execute(sql, params)
        rows = result.mappings().all()

    courses: list[Course] = []
    for row in rows:
        data = {k: v for k, v in row.items() if k != 'distance'}
        course = Course(**data)
        course.distance = row['distance']
        courses.append(course)

    return courses

def keyword_search(query: str, engine: Engine, threshold: float = 0.1, limit: int = 5) -> list[Course]:
    with engine.connect() as conn:
        keyword_results = conn.execute(
            TF_IDF_SEARCH_QUERY,
            {"query_text": query, "threshold": threshold, "limit": limit}
        )
        rows = keyword_results.mappings().all()

    return [Course(**row) for row in rows]

def bm25_search(query: str, engine: Engine, limit: int = 5, k1: float = 0.9, b: float = 0.3) -> list[Course]:
    bm25_results = search_courses_bm25(query, engine, limit, k1, b)
    return [Course(**row) for row in bm25_results]
