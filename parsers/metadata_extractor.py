import re

import pandas as pd


def extract_learner_count(text) -> int | None:
    """
    Extracts the number of learners from a string like:
    '229,993 learners have completed this activity in the past 12 months'

    Returns:
        int: The extracted number of learners, or None if not found.
    """
    if not isinstance(text, str) or pd.isna(text) or not text.strip():
        return None

    match = re.search(r"\b(\d{1,10})\b", text)
    return int(match.group(1)) if match else None


def extract_star_rating(text) -> float | None:
    """
    Extracts the average star rating from a string like:
    'Average rating of 4.5 stars by 4267 learners in the past 12 months.'

    Returns:
        float: The extracted rating (e.g. 4.5), or None if not found.
    """
    if not isinstance(text, str) or pd.isna(text) or not text.strip():
        return None

    match = re.search(r"\b(\d+(\.\d+)?)\s*stars?\b", text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_numeric(value) -> int | None:
    """
    Extracts digits from a value. Returns an int or None if no digits found.
    """
    if pd.isna(value):
        return None
    digits = re.sub(r"\D", "", str(value))
    return int(digits) if digits.isdigit() else None