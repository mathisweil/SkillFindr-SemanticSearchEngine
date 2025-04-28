import math
from collections import Counter, defaultdict
from typing import List, Callable, Sequence

Tokeniser = Callable[[str], List[str]]

def simple_tokeniser(text: str) -> List[str]:
    """Lower-case, split on ASCII word boundaries."""
    import re
    return re.findall(r"\b\w+\b", text.lower())

class BM25:
    def __init__(
        self,
        corpus: Sequence[str],
        *,
        tokenizer: Tokeniser = simple_tokeniser,
        k1: float = 1.2,
        b: float = 0.75,
    ) -> None:
        self.k1, self.b = k1, b
        self.tok = tokenizer

        # --- Pre-compute corpus statistics -------------------------------
        self.doc_tokens: List[List[str]] = [self.tok(doc) for doc in corpus]
        self.doc_lens: List[int] = [len(toks) for toks in self.doc_tokens]
        self.avgdl: float = sum(self.doc_lens) / len(self.doc_lens)

        # Term document frequency n_i
        self.doc_freqs: defaultdict[str, int] = defaultdict(int)
        for toks in self.doc_tokens:
            for term in set(toks):
                self.doc_freqs[term] += 1

        self.N: int = len(self.doc_tokens)

        # Pre-compute IDF weights
        self.idf: dict[str, float] = {
            term: math.log((self.N - n + 0.5) / (n + 0.5) + 1.0)
            for term, n in self.doc_freqs.items()
        }

        # Cache per-document term counts
        self.tfs: List[Counter[str]] = [Counter(toks) for toks in self.doc_tokens]

    # --------------------------------------------------------------------
    def score_single(self, tf: Counter[str], dl: int, query_terms: List[str]) -> float:
        score = 0.0
        for term in query_terms:
            if term not in tf:
                continue
            freq = tf[term]
            idf = self.idf.get(term, 0.0)  # unseen term → 0
            denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

    def score(self, query: str, top_k: int | None = None) -> List[tuple[int, float]]:
        q_terms = self.tok(query)
        scores = [
            (idx, self.score_single(tf, dl, q_terms))
            for idx, (tf, dl) in enumerate(zip(self.tfs, self.doc_lens))
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores if top_k is None else scores[:top_k]
