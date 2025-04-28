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
# BM25 / TF-IDF STYLE SEARCH (With tags as TEXT[])
# -----------------------------------
BM25_SEARCH_QUERY = text("""
WITH search_vectors AS (
    SELECT
        course_id,
        title,
        course_url,
        description,
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||  -- Title highly weighted
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||  -- Description moderately weighted
        setweight(to_tsvector('english', array_to_string(coalesce(tags, '{}'), ' ')), 'C') AS document  -- Tags lightly weighted
    FROM courses
)
SELECT
    course_id,
    title,
    course_url,
    description,
    bm25(
        document,
        websearch_to_tsquery('english', :query_text),
        1.2,   -- k1 hyperparameter (term frequency scaling)
        0.75   -- b hyperparameter (document length normalization)
    ) AS rank
FROM search_vectors
WHERE document @@ websearch_to_tsquery('english', :query_text)
  AND bm25(
        document,
        websearch_to_tsquery('english', :query_text),
        1.2,
        0.75
    ) > :threshold
ORDER BY rank DESC
LIMIT :limit
""")



BM25_CANDIDATE_QUERY = text("""
SELECT
    course_id,
    title,
    course_url,
    description,
    -- raw tsvector needed for length statistics in Python
    document
FROM   search.course_vectors
WHERE  document @@ websearch_to_tsquery('english', :query_text)
LIMIT  :candidate_limit          -- e.g. 2-3× the final k you want to return
""")



BM25_SEARCH_QUERY_OR = text("""
WITH q AS (
  SELECT to_tsquery(
           'english',
           replace(
             regexp_replace(:query_text, '\\s+', ' ', 'g'),
             ' ',
             ' | '
           )
         ) AS query
),
docs AS (
  SELECT
    course_id,
    title,
    description,
    tags,
    setweight(to_tsvector('english', coalesce(title, '')),       'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
    setweight(
      to_tsvector('english', coalesce(array_to_string(tags, ' '), '')),
      'C'
    ) AS document
  FROM courses
)
SELECT
  course_id,
  title,
  description,
  tags,
  ts_rank_cd(document, q.query) AS rank
FROM docs
CROSS JOIN q
WHERE
  docs.document @@ q.query
  AND ts_rank_cd(document, q.query) > :threshold
ORDER BY rank DESC
LIMIT :limit;
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
        ts_rank_cd(to_tsvector(embedding_input_combined), plainto_tsquery(:query_text)) AS rank
    FROM courses
    WHERE to_tsvector(embedding_input_combined) @@ plainto_tsquery(:query_text)
),
combined AS (
    SELECT
        v.course_id,
        v.title,
        v.course_url,
        v.description,
        v.distance,
        t.rank,
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