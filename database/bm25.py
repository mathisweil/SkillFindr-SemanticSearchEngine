import math
from typing import Any
from collections import Counter

from sqlalchemy import MetaData, Table, select
from sqlalchemy.engine import Engine

import spacy
import nltk
from nltk.corpus import wordnet as wn


_courses: Table = None
_nlp: spacy.language.Language = None


def setup_environment(engine: Engine):
    """
    Load NLP models, NLTK data, and reflect the 'courses' table.
    Must be called once per process (or per new engine).
    """
    global _courses, _nlp

    metadata = MetaData()
    _courses = Table("courses", metadata, autoload_with=engine)

    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

    _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])


def preprocess(text: str) -> list[str]:
    """
    Lemmatise, lowercase, remove stopwords & non-alphabetic tokens,
    and keep only NOUN/VERB/ADJ/PROPN.
    """
    doc = _nlp(text.lower())
    return [
        token.lemma_ for token in doc
        if token.is_alpha and not token.is_stop and token.pos_ in {"NOUN", "VERB", "ADJ", "PROPN"}
    ]


def get_synonyms(term: str, max_synonyms: int = 3) -> set:
    synsets = wn.synsets(term)
    lemmas = [lemma.name().replace('_', ' ') for syn in synsets for lemma in syn.lemmas()]
    unique_lemmas = list(dict.fromkeys(lemmas))
    return set(unique_lemmas[:max_synonyms]) - {term}


def expand_query(terms: list[str]) -> list[str]:
    """
    Expand the original terms set with their WordNet synonyms.
    """
    expanded = set(terms)
    for term in terms:
        expanded |= get_synonyms(term)
    return list(expanded)


def bm25_score(
    query_terms: list[str],
    doc_terms: list[str],
    avgdl: float,
    k1: float = 1.2,
    b: float = 0.75,
    N: int = 1,
    df: dict[str, int] = None
) -> float:
    """
    Compute BM25 score for a single document.
    """
    df = df or {}
    freqs = Counter(doc_terms)
    score = 0.0

    for term in query_terms:
        f = freqs.get(term, 0)
        n = df.get(term, 0)
        idf = math.log((N - n + 0.5) / (n + 0.5) + 1)
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * (len(doc_terms) / avgdl))
        score += idf * (numerator / denominator)

    return score


def search_courses_bm25(
    query: str,
    engine: Engine,
    limit: int = 5,
    k1: float = 1.2,
    b: float = 0.75
) -> list[dict[str, Any]]:
    if _courses is None or _nlp is None:
        setup_environment(engine)

    lemmas = preprocess(query)
    if not lemmas:
        return []

    expanded_terms = expand_query(lemmas)

    stmt = select(_courses)
    for term in lemmas:
        stmt = stmt.where(_courses.c.embedding_input_combined.ilike(f"%{term}%"))

    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

    if not rows:
        return []

    documents = [
        preprocess(row['embedding_input_combined'] or "")
        for row in rows
    ]
    N = len(documents)
    avgdl = sum(len(doc) for doc in documents) / N if N > 0 else 1.0

    df = Counter()
    for doc in documents:
        for term in set(doc):
            df[term] += 1

    scored = []
    for idx, row in enumerate(rows):
        score = bm25_score(expanded_terms, documents[idx], avgdl, k1, b, N=N, df=df)
        result = dict(row)
        result['bm25_score'] = score
        scored.append(result)

    scored.sort(key=lambda x: x['bm25_score'], reverse=True)
    return scored[:limit]
