from sqlalchemy import text

# -------------------------------
# VECTOR-BASED SEMANTIC SEARCH
# -------------------------------
SEMANTIC_SEARCH_QUERY = text("""
WITH matches AS (
    SELECT
        course_id,
        title,
        course_url,
        description,
        embedding_vector <=> :query_vector AS distance
    FROM courses
    WHERE embedding_vector <=> :query_vector < :threshold
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


# -------------------------------
# BM25 / TF-IDF STYLE SEARCH
# -------------------------------
BM25_SEARCH_QUERY = text("""
SELECT
    course_id,
    title,
    course_url,
    description,
    ts_rank_cd(embedding_input_tsv, plainto_tsquery(:query_text)) AS rank
FROM courses
WHERE embedding_input_tsv @@ plainto_tsquery(:query_text)
ORDER BY rank DESC
LIMIT :limit
""")


# -------------------------------
# HYBRID SEARCH (COMBINED SIGNALS)
# -------------------------------
HYBRID_SEARCH_QUERY = text("""
WITH vector_matches AS (
    SELECT
        course_id,
        title,
        course_url,
        description,
        embedding_vector <#> :query_vector AS distance
    FROM courses
    WHERE embedding_vector <#> :query_vector < :threshold
),
text_matches AS (
    SELECT
        course_id,
        ts_rank_cd(embedding_input_tsv, plainto_tsquery(:query_text)) AS rank
    FROM courses
    WHERE embedding_input_tsv @@ plainto_tsquery(:query_text)
),
combined AS (
    SELECT
        v.course_id,
        v.title,
        v.course_url,
        v.description,
        v.distance,
        t.rank,
        -- You can weight these however you like
        (1 - v.distance) * 0.6 + t.rank * 0.4 AS score
    FROM vector_matches v
    JOIN text_matches t ON v.course_id = t.course_id
)
SELECT * FROM combined
ORDER BY score DESC
LIMIT :limit
""")
