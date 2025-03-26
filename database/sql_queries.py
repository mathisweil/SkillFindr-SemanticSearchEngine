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
    ts_rank_cd(to_tsvector(embedding_input), plainto_tsquery(:query_text)) AS rank
FROM courses
WHERE to_tsvector(embedding_input) @@ plainto_tsquery(:query_text)
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


# -------------------------------
# CREATE COURSE TABLE
# -------------------------------
CREATE_TABLE_QUERY = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_url TEXT,
    category TEXT,
    type TEXT,
    title TEXT,
    duration INTEGER,
    learners_amount INTEGER,
    star_rating REAL,
    star_num_ratings INTEGER,
    description TEXT,
    tags TEXT[],
    title_raw TEXT,
    description_raw TEXT,
    languages TEXT[],
    tags_raw TEXT[],
    embedding_input_combined TEXT,
    embedding_vector VECTOR(384)
);
"""


# -------------------------------
# INSERT INTO COURSE TABLE
# -------------------------------
INSERT_QUERY = text("""
INSERT INTO courses (
    course_id, course_url, category, type, title, duration, learners_amount, star_rating, star_num_ratings,
    description, tags, title_raw, description_raw, languages, tags_raw, embedding_input_combined, embedding_vector
) VALUES (
    :course_id, :course_url, :category, :type, :title, :duration, :learners_amount, :star_rating, :star_num_ratings,
    :description, :tags, :title_raw, :description_raw, :languages, :tags_raw, :embedding_input_combined, :embedding_vector
)
ON CONFLICT (course_id)
DO UPDATE SET 
    course_url = EXCLUDED.course_url,
    category = EXCLUDED.category,
    type = EXCLUDED.type,
    title = EXCLUDED.title,
    duration = EXCLUDED.duration,
    learners_amount = EXCLUDED.learners_amount,
    star_rating = EXCLUDED.star_rating,
    star_num_ratings = EXCLUDED.star_num_ratings,
    description = EXCLUDED.description,
    tags = EXCLUDED.tags,
    title_raw = EXCLUDED.title_raw,
    description_raw = EXCLUDED.description_raw,
    languages = EXCLUDED.languages,
    tags_raw = EXCLUDED.tags_raw,
    embedding_input_combined = EXCLUDED.embedding_input_combined,
    embedding_vector = EXCLUDED.embedding_vector;
""")