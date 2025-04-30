from sqlalchemy import text

# -------------------------------
# VECTOR-BASED SEMANTIC SEARCH (without filters)
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


# -----------------------------------
# TF-IDF STYLE SEARCH
# -----------------------------------
TF_IDF_SEARCH_QUERY = text("""
WITH search_vectors AS (
    SELECT
        course_id,
        title,
        course_url,
        description,
        embedding_input_combined,
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', array_to_string(coalesce(tags, ARRAY[]::TEXT[]), ' ')), 'C') AS document
    FROM courses
)
SELECT
    course_id,
    title,
    course_url,
    description,
    embedding_input_combined,
    ts_rank_cd(document, websearch_to_tsquery('english', :query_text)) AS rank
FROM search_vectors
WHERE document @@ websearch_to_tsquery('english', :query_text)
  AND ts_rank_cd(document, websearch_to_tsquery('english', :query_text)) > :threshold
ORDER BY rank DESC
LIMIT :limit
""")


# -------------------------------
# CREATE COURSE TABLE
# -------------------------------
CREATE_TABLE_QUERY = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_url TEXT NOT NULL UNIQUE,
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