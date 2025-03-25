import re
import html
import unicodedata
import codecs

import ftfy
import pandas as pd
import langcodes
from pathlib import Path

from bs4 import BeautifulSoup

from utils.config import load_config
from utils.io_utils import save_data, load_data


BOILERPLATE = [
    # Completion & Progress Instructions
    "after you complete this activity",
    "return to this page to select mark complete",
    "for completion credit",
    "you will get completion credit in the ibm security learning academy",
    "you have the option to complete the web development fundamentals courses",
    "after completing this course, you should be able to",
    "after completing cybersecurity fundamentals, you should be able to",
    "you will find short instructional content offerings",
    "you will be prompted to log in",
    "for first time users, your user id must be the email address linked to your ibmid",
    "complete the following modules to earn an industry-recognized ibm skillsbuild digital credential",
    "complete this course to earn the cybersecurity fundamentals badge",
    # Introductory/Descriptive
    "about this learning activity",
    "about this digital credential",
    "disclaimer",
    "learning outcomes",
    "level: beginner",
    "presentation slides",
    "resources",
    "prerequisite: none",
    "there is an updated version of this course in the following",
    "there is an updated version of this course",
    # Subtitles / Language Settings
    "note: on the video toolbar",
    "go to settings",
    "select subtitles",
    "select english",
    "auto-translate",
    "enable subtitles",
    "language of your choice",
    "from the drop-down",
    "this activity is available only in english",
    "this newly designed experience is",
    # Legal Disclaimers
    "any presentation by the presenting lawyers",
    "should not be considered or construed as legal advice",
    "receipt of it does not constitute an attorney-client relationship",
    "the contents of this document are intended for general information purposes only",
    # Badging / Enrolment
    "badge opportunity",
    "badges:",
    "click enroll",
    "click the enroll me button",
    "click here to take it",
    "select enroll",
    "select start tracking progress",
    "complete the courses in order",
    "courses: 3",
    "you agree to the following",
    "to enroll in this learning plan and get started",
    # Introductory Fluff
    "have fun exploring",
    "curious about tech, but not sure where to focus",
    "in this recorded webinar, you will",
    "webinar summary",
    "what you’ll learn",
    # Course Provider Mentions
    "this article is presented by indeed career guide",
    "this course is presented by openclassrooms",
    "this course is presented by w3schools",
    "this resource is presented by w3schools",
    "this video is presented by 365 data science",
    "this video is presented by edureka",
    "this video is presented by simplilearn",
    "this video is presented by freecodecamp.org",
    "presented by professor messer",
    "presented by red hat",
    "this learning activity is presented by khan academy",
    "this course requires you register for an ibmid to access",
    "it is presented by edureka",
    # Miscellaneous
    "the topics include",
    "this is a curation of eight course units",
    "overview of data tools and languages",
    "duration: 7 hours, 10 minutes",
    "duration: complete the activities in this course and earn 30 minutes of learning credit!",
    "the content is offered in english",
    "languages:",
    "language:",
    "note:",
    # Specific Redundant Phrases
    "> when you complete all courses, be sure to return to page to select mark complete for completion credit on ibm skillsbuild",
    "start with the get the details! resource to discover if this program is right for you",
    "getting started in cybersecurity is ideal for individuals in non-technical job positions",
    "technical introduction to cybersecurity is ideal for individuals in technical roles",
    "you will need to register for a free account",
    "get a feel for cybersecurity as a career",
    "and then select auto-translate to enable subtitles in a language of your choice from the drop-down",
]

boilerplate_pattern = re.compile(
    r"|".join(rf"\s*{re.escape(phrase)}[\s\.,;:!?\u2026\u3002]*" for phrase in BOILERPLATE),
    flags=re.IGNORECASE
)

duration_pattern = re.compile(
    r"(?:duration|expected duration)\s*:\s*"
    r"(complete the activities.*?learning credit!|"
    r"(?:this course will take you about\s*)?\d+\s*(hours?|hrs?|h|minutes?|mins?|m)"
    r"(?:,\s*\d+\s*(minutes?|mins?|m))?)",
    flags=re.IGNORECASE
)

language_span_pattern = re.compile(
    r"(languages\s*:|available in|here\s*:|a version of this course is available in)\s*((?:[^.:;\n]|[ -￿])+)",
    flags=re.IGNORECASE
)

learners_pattern = re.compile(
    r"(?:\b[a-z]+\s+)?learners?\s+can\s+complete\s+the\s+learning(?:\s+here:)?",
    flags=re.IGNORECASE
)

def extract_languages_from_soup(soup: BeautifulSoup) -> list[str]:
    """
    Extract language codes from HTML tags with a 'lang' attribute.
    """
    langs = set()
    for tag in soup.find_all(attrs={"lang": True}):
        lang_value = tag.get("lang")
        if lang_value:
            try:
                language = langcodes.get(lang_value)
                if language and language.language:
                    langs.add(language.language.lower())
                else:
                    langs.add(lang_value.lower())
            except Exception:
                langs.add(lang_value.lower())
    return list(langs)


def extract_iso_languages(text: str) -> tuple[str, list[str]]:
    """
    Extract ISO language codes from the text based on language mentions.
    """
    if not isinstance(text, str):
        return text, []

    modified_text = text
    candidates = [candidate.strip(" .;:,") for candidate in re.split(r',|\band\b', text) if candidate.strip()]
    iso_langs = set()
    for candidate in candidates:
        try:
            language = langcodes.find(candidate)
            if language and language.language:
                iso_langs.add(language.language.lower())
                modified_text = re.sub(r'\b' + re.escape(candidate) + r'\b', '', modified_text, flags=re.IGNORECASE)
        except Exception:
            continue

    modified_text = re.sub(r'\s+', ' ', modified_text).strip()
    return modified_text, list(iso_langs)


def clean_description(text: str) -> tuple[str, list[str]]:
    """
    Clean a description by decoding HTML, normalising Unicode, removing URLs, long numeric strings,
    durations, and boilerplate phrases.
    """
    if not isinstance(text, str):
        return text, []

    soup = BeautifulSoup(text, "html.parser")

    for tag in soup(["script", "style", "header", "footer", "nav", "noscript"]):
        tag.decompose()

    languages_from_html = extract_languages_from_soup(soup)

    text = soup.get_text(separator=" ")
    text = html.unescape(text).lower()

    text, languages_from_text = extract_iso_languages(text)

    try:
        text = codecs.decode(text, 'unicode_escape')
    except Exception:
        pass
    text = unicodedata.normalize("NFKC", text)
    text = ftfy.fix_text(text)
    text = ftfy.fix_encoding(text)
    text = re.sub(r'[\u2020\u0304\u00a0]+', ' ', text)

    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\d{5,}", "", text)

    text = language_span_pattern.sub(" ", text)
    text = duration_pattern.sub(" ", text)
    text = boilerplate_pattern.sub(" ", text)
    text = learners_pattern.sub(" ", text)

    languages = set(languages_from_html).union(set(languages_from_text))
    if len(languages) == 0:
        languages.add("en")

    text = re.sub(r'([,.!?;:])\1+', r'\1', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, list(languages)


def clean_text(text: str) -> str | None:
    """
    Remove HTML tags and excess whitespace from the input text.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text.strip())


def convert_duration(duration: str) -> int:
    """
    Convert a duration string into total minutes.
    Returns None if the conversion is not possible.
    """
    if pd.isna(duration) or not isinstance(duration, str):
        return 0

    duration = duration.lower().strip()
    duration = re.sub(r"[^\w\s:]", "", duration)  # Remove punctuation.

    minutes = 0

    hr_match = re.search(r"(\d+)\s*(?:h(?:ours?)?|hr)", duration)
    if hr_match:
        minutes += int(hr_match.group(1)) * 60

    min_match = re.search(r"(\d+)\s*m(?:in(?:utes?)?)?", duration)
    if min_match:
        minutes += int(min_match.group(1))

    return minutes if minutes > 0 else None


def clean_title(text: str) -> str:
    """
    Clean a title by fixing encoding issues, removing boilerplate phrases, and normalising whitespace and punctuation.
    """
    if not isinstance(text, str):
        return text

    text = ftfy.fix_text(text)
    text = clean_text(text)

    text = text.lower()

    boilerplate_phrases = [
        r"\(\s*earn a credential!?[\s]*\)",
        r"\(\s*earn a badge!?[\s]*\)",
        r"\(\s*new design; earn a credential!?[\s]*\)",
    ]
    for pattern in boilerplate_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[.,;:!?]+$", "", text)


def clean_tags(tags) -> list[str]:
    """
    Cleans and normalises a list of tags.
    Returns an empty list if tags is None or invalid.
    """
    if not isinstance(tags, list):
        return []

    cleaned = set()
    for tag in tags:
        if isinstance(tag, str):
            normalised = tag.strip().lower()
            if normalised:
                cleaned.add(normalised)

    return list(cleaned)


def extract_numeric(value) -> int:
    """
    Extract numeric value from the input by removing non-digit characters.
    """
    if pd.isna(value):
        return 0
    value = re.sub(r"[^\d]", "", str(value))
    return int(value) if value.isdigit() else 0


def main():
    config = load_config()
    df = load_data(config['raw_output_path'])

    df = df[df["course_url"].notnull()]
    df["course_id"] = df["course_url"].apply(lambda url: url.split("/")[-1] if isinstance(url, str) else None)
    df = df[df["course_id"].notnull()]

    df = df.drop_duplicates(subset="course_id")

    df["title_raw"] = df["title"]
    df["title"] = df["title"].apply(lambda x: clean_title(x) if isinstance(x, str) and x.strip() else "Untitled")

    df["description_raw"] = df["description"]
    df[["description", "languages"]] = df["description"].apply(
        lambda x: pd.Series(
            clean_description(x) if isinstance(x, str) and x.strip() else ("no description available", ["en"]))
    )

    df["tags_raw"] = df["tags"]
    df["tags"] = df["tags"].apply(lambda x: clean_tags(x) if isinstance(x, list) else [])

    df["duration"] = df["duration"].apply(lambda x: convert_duration(x) if isinstance(x, str) else 0)
    df["learners_amount"] = df["learners_amount"].apply(lambda x: extract_numeric(x) if pd.notnull(x) else 0)
    df["star_rating"] = df["star_rating"].apply(
        lambda x: float(re.search(r"(\d+(\.\d+)?)", str(x)).group(1))
        if isinstance(x, str) and re.search(r"(\d+(\.\d+)?)", x)
        else float(x) if isinstance(x, (int, float)) and not pd.isna(x)
        else 0.0
    )
    df["star_num_ratings"] = df["star_num_ratings"].apply(lambda x: extract_numeric(x) if pd.notnull(x) else 0)

    df = df.sort_values(by=["learners_amount", "star_rating"], ascending=[False, False])

    processed_dir = Path(config['processed_output_path'])
    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_filename = processed_dir / "processed_courses.csv"
    json_filename = processed_dir / "processed_courses.json"
    save_data(df, csv_filename, json_filename)


if __name__ == "__main__":
    main()
