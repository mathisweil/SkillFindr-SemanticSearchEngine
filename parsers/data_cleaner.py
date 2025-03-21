from datetime import datetime
import re
import html
import unicodedata
import codecs

import ftfy
import pandas as pd
import langcodes

from utils.config import load_config


def load_data():
    """
    Load configuration and JSON data from the raw output file.
    Uses the current date in the filename.
    """
    config = load_config()
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_path = f"../{config['raw_output_path']}/{config['output_filename']}_2025-03-12.json"
    return config, pd.read_json(file_path)


# List of boilerplate phrases to remove from text fields.
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
    # Introductory/Descriptive
    "about this learning activity",
    "about this digital credential",
    "disclaimer",
    "learning outcomes",
    "level: beginner",
    "presentation slides",
    "resources",
    "prerequisite: none",
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
    "select enroll",
    "select start tracking progress",
    "complete the courses in order",
    "courses: 3",
    "you agree to the following",
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
    "cyber attacks",
    "cybersecurity: on the defense",
    "cybersecurity: on the offense",
    "data encryption techniques",
    "pii (personally identifiable information)",
    "user authentication methods",
    "user data tracking",
    "secure internet protocols",
    "introduction to online data security",
    "describe cybersecurity, the cia triad",
    "recognize the cybersecurity job market",
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
]

# Compile boilerplate regex pattern.
boilerplate_pattern = re.compile(
    r"|".join(rf"\s*{re.escape(phrase)}[\s\.,;:!?\u2026\u3002]*" for phrase in BOILERPLATE),
    flags=re.IGNORECASE
)

# Pattern to remove duration strings.
duration_pattern = re.compile(
    r"duration:\s*(complete the activities.*?learning credit!|\d+\s*(hours?|hrs?|h|mins?|minutes?|m)(,\s*\d+\s*(minutes?|mins?|m))?)",
    flags=re.IGNORECASE
)


def clean_description(text: str) -> str:
    """
    Clean a description by decoding HTML, normalising unicode, removing URLs, long numeric strings,
    durations, and boilerplate phrases.
    """
    if not isinstance(text, str):
        return text

    # Decode HTML entities and unicode escape sequences.
    text = html.unescape(text)
    try:
        text = codecs.decode(text, 'unicode_escape')
    except Exception:
        pass  # Skip if already decoded.

    # Normalise unicode and fix encoding issues.
    text = unicodedata.normalize("NFKC", text)
    text = ftfy.fix_text(text)
    text = text.replace('\u00a0', ' ')

    # Lowercase for standardisation.
    text = text.lower()

    # Remove URLs and long numeric strings.
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\d{5,}", "", text)

    # Remove durations and boilerplate content.
    text = duration_pattern.sub(" ", text)
    text = boilerplate_pattern.sub(" ", text)

    # Clean up excess whitespace.
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """
    Remove HTML tags and excess whitespace from the input text.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text.strip())


def extract_iso_languages(text: str) -> list:
    """
    Extract ISO language codes from the text based on language mentions.
    """
    match = re.search(r'languages?:\s*(.*)', text, re.IGNORECASE)
    if not match:
        return []
    raw_langs = re.split(r',|\band\b', match.group(1), flags=re.IGNORECASE)
    cleaned_langs = [lang.strip() for lang in raw_langs if lang.strip()]

    iso_langs = []
    for lang in cleaned_langs:
        try:
            language = langcodes.find(lang)
            if language.language:
                iso_langs.append(language.language)
        except Exception:
            continue
    return iso_langs


def convert_duration(duration: str) -> int:
    """
    Convert a duration string into total minutes.
    Returns None if the conversion is not possible.
    """
    if pd.isna(duration) or not isinstance(duration, str):
        return None

    duration = duration.lower().strip()
    duration = re.sub(r"[^\w\s:]", "", duration)  # Remove punctuation.

    minutes = 0

    hr_match = re.search(r"(\d+)\s*(?:h(?:ours?)?|hr)", duration)
    if hr_match:
        minutes += int(hr_match.group(1)) * 60

    min_match = re.search(r"(\d+)\s*(?:m(?:in(?:utes?)?)?)", duration)
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

    # Lowercase for consistency.
    text = text.lower()

    # Remove specific boilerplate phrases from titles.
    boilerplate_phrases = [
        r"\(\s*earn a credential!?[\s]*\)",
        r"\(\s*earn a badge!?[\s]*\)",
        r"\(\s*new design; earn a credential!?[\s]*\)",
    ]
    for pattern in boilerplate_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Final cleanup: remove excess whitespace and trailing punctuation.
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[.,;:!?]+$", "", text)


def extract_numeric(value) -> int:
    """
    Extract numeric value from the input by removing non-digit characters.
    """
    if pd.isna(value):
        return 0
    value = re.sub(r"[^\d]", "", str(value))
    return int(value) if value.isdigit() else 0


def main():
    config, df = load_data()

    # Apply cleaning functions to DataFrame columns.
    df["title"] = df["title"].apply(clean_title)
    df["description"] = df["description"].apply(lambda x: clean_description(x) if isinstance(x, str) else None)
    df["duration"] = df["duration"].apply(convert_duration)
    df["learners_amount"] = df["learners_amount"].apply(extract_numeric)
    df["star_rating"] = df["star_rating"].apply(
        lambda x: float(re.search(r"(\d+(\.\d+)?)", str(x)).group(1))
        if isinstance(x, str) and re.search(r"(\d+(\.\d+)?)", x)
        else 0.0
    )
    df["star_num_ratings"] = df["star_num_ratings"].apply(extract_numeric)
    df["languages"] = df["description"].apply(lambda x: extract_iso_languages(x) if isinstance(x, str) else None)

    # Sort DataFrame by learners amount and star rating in descending order.
    df = df.sort_values(by=["learners_amount", "star_rating"], ascending=[False, False])

    # Save processed data.
    output_json_path = f"../{config['processed_output_path']}/{config['output_filename']}.json"
    output_csv_path = f"../{config['processed_output_path']}/{config['output_filename']}.csv"
    df.to_json(output_json_path, orient="records", indent=4)
    df.to_csv(output_csv_path, index=False)


if __name__ == "__main__":
    main()
