import re
import html

import ftfy
import pandas as pd


def clean_title(text: str) -> str:
    """
    Cleans a course title: encoding fixes, removal of boilerplate phrases,
    punctuation trimming, and whitespace normalisation.
    Returns an empty string if input is invalid.
    """
    if not isinstance(text, str):
        return ""
    text = ftfy.fix_text(text)
    text = clean_text(text) or ""

    text = text.lower()
    boilerplate_phrases = [
        r"\(\s*earn a credential!?[\s]*\)",
        r"\(\s*earn a badge!?[\s]*\)",
        r"\(\s*new design; earn a credential!?[\s]*\)",
    ]
    for pattern in boilerplate_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"[.,;:!?]+$", "", text)
    return text.strip()


def clean_tags(tags) -> list[str]:
    """
    Normalises a list of tags to lowercase, stripped strings.
    Returns an empty list if input is invalid.
    """
    if not isinstance(tags, list):
        return []
    cleaned = {tag.strip().lower() for tag in tags if isinstance(tag, str) and tag.strip()}
    return list(cleaned)


def clean_text(text: str) -> str | None:
    """
    Clean text by unescaping HTML, removing tags, and normalising whitespace.
    Returns None if input is not valid.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text.strip())


def convert_duration(duration: str | int | float | None) -> int | None:
    """
    Convert duration from string (e.g., '2 hours 30 minutes') to total minutes.
    Returns None if conversion is not possible.
    """
    if pd.isna(duration):
        return None
    if isinstance(duration, (int, float)):
        return int(duration)

    if not isinstance(duration, str):
        return None

    duration = duration.lower().strip()
    duration = re.sub(r"[^\w\s:]", "", duration)

    minutes = 0

    day_match = re.search(r"(\d+)\s*d(?:ays?)?", duration)
    hr_match = re.search(r"(\d+)\s*(?:h(?:ours?)?|hr)", duration)
    min_match = re.search(r"(\d+)\s*m(?:in(?:utes?)?)?", duration)

    if day_match:
        minutes += int(day_match.group(1)) * 1440
    if hr_match:
        minutes += int(hr_match.group(1)) * 60
    if min_match:
        minutes += int(min_match.group(1))

    return minutes if minutes > 0 else None