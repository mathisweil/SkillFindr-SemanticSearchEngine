import re
import html


def clean_text(text):
    """
    General text cleaning function.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def clean_type(type_text):
    """
    Cleans the type field.
    """
    return type_text.strip().lower().replace(' ', '_') if type_text else None


def clean_duration(duration_text):
    """
    Cleans the duration field by extracting hours and minutes from a text string.
    """
    if not duration_text or not duration_text.strip():
        return None

    duration_text = clean_text(duration_text)

    hours_match = re.search(r'(\d+)\s*(?:hrs?|hours?)', duration_text, re.IGNORECASE)
    hours = int(hours_match[1]) if hours_match else 0

    minutes_match = re.search(r'(\d+)\s*(?:mins?|minutes?)', duration_text, re.IGNORECASE)
    minutes = int(minutes_match[1]) if minutes_match else 0

    total_seconds = (hours * 3600) + (minutes * 60)

    return total_seconds if total_seconds > 0 else None


def clean_learners_amount(learners_amount):
    """
    Cleans the 'learners_amount' field by extracting the first numeric value
    from the provided text and converting it to an integer.
    """
    if not isinstance(learners_amount, str) or not learners_amount.strip() or learners_amount.strip().upper() == "N/A":
        return None

    if match := re.search(r'\d[\d,]*', learners_amount):
        numeric_str = match.group().replace(',', '')
        return int(numeric_str)
    return None


def clean_star_rating(star_rating):
    """
    Extracts the numeric star rating from a descriptive string.
    """
    if not isinstance(star_rating, str) or not star_rating.strip():
        return None

    star_rating = clean_text(star_rating)

    match = re.search(r'([0-9]*\.?[0-9]+)', star_rating)
    return float(match[1]) if match else None


def clean_star_num_ratings(star_num_ratings):
    """
    Cleans the 'star_num_ratings' field by removing extraneous characters
    """
    if not isinstance(star_num_ratings, str) or not star_num_ratings.strip() or star_num_ratings.strip().upper() == "N/A":
        return None
    digits = re.sub(r'\D', '', star_num_ratings)
    return int(digits) if digits else None


UNWANTED_TAGS = {
    "000 All digital credentials", "000 All digital credentials - Academia"
}

def clean_tags(tag_list):
    """Cleans and deduplicates course tags."""
    if not isinstance(tag_list, list):
        return []
    cleaned_tags = [tag.strip() for tag in tag_list if tag.strip() and tag not in UNWANTED_TAGS]
    return sorted(set(cleaned_tags))


def clean_raw_description(raw_html):
    """
    Returns the raw HTML description **without** any cleaning or modifications.
    """
    return raw_html.strip() if isinstance(raw_html, str) else None


# def clean_description(description_text):
#     """Cleans course descriptions and extracts embedded language information."""
#     if not isinstance(description_text, str) or not description_text.strip():
#         return {"description": "", "languages": []}
#
#     cleaned_text = clean_text(description_text)
#
#     cleaned_text = re.sub(r'(?i)^About this (learning activity|credential|course|specialization|training|certification|module|professional certificate|guided project|badge|program|exam|learning plan|skills track|pathway)\s*', '', cleaned_text)
#
#     languages_found = []
#
#     note_match = re.search(r'(?i)Note:\s*.*?available in\s*([^.]+)\.', cleaned_text)
#     if note_match:
#         languages_found.append(note_match[1])
#         cleaned_text = re.sub(r'(?i)Note:\s*.*?available in\s*([^.]+)\.', '', cleaned_text)
#
#     language_patterns = [
#         r'(?i)(Languages?:)\s*([^.]+)',
#         r'(?i)available in (?:these languages here:\s*)?([^.]+)'
#     ]
#     for pattern in language_patterns:
#         matches = re.findall(pattern, cleaned_text)
#         for match in matches:
#             if isinstance(match, tuple):
#                 languages_found.append(match[1])
#             else:
#                 languages_found.append(match)
#             cleaned_text = re.sub(pattern, '', cleaned_text)
#
#     unwanted_phrases = [
#         r'(?i)Select Enroll.*$',
#         r'(?i)Click here to take it.*$',
#         r'(?i)Start tracking progress to enroll.*$',
#         r'(?i)A version of this course is available in these languages here:.*?Description',
#         r'(?i)Complete this course to earn.*?$',
#         r'(?i)Earn your digital credentials.*$',
#         r'(?i)You will receive digital badges.*$',
#         r'(?i)When you complete all courses, be sure to.*$',
#     ]
#     for phrase in unwanted_phrases:
#         cleaned_text = re.sub(phrase, '', cleaned_text).strip()
#
#     cleaned_text = re.sub(r'(?i)What you’ll learn\s*', 'Learning Objectives: ', cleaned_text)
#     cleaned_text = re.sub(r'(?i)A version of this course is available.*?:', '', cleaned_text)
#     cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
#
#     languages_list = sorted(set(
#         l.strip() for lang in languages_found for l in re.split(r'\s*and\s*|\s*,\s*', lang) if l.strip()
#     ))
#
#     return {"description": cleaned_text, "languages": clean_languages(languages_list)}
#
#
# VALID_LANGUAGES = {
#     "English", "French", "Spanish", "German", "Italian", "Japanese", "Portuguese",
#     "Arabic", "Dutch", "Hindi", "Polish", "Turkish", "Ukrainian", "Czech",
#     "Chinese (Traditional)", "Chinese (Simplified)"
# }
#
#
# def clean_languages(language_list):
#     """Cleans and standardizes the list of extracted languages."""
#     if not isinstance(language_list, list):
#         return []
#
#     cleaned_languages = []
#     for lang in language_list:
#         lang = lang.strip()
#
#         if re.search(r"portuguese.*brazil", lang, re.IGNORECASE):
#             lang = "Brazilian Portuguese"
#         elif "Portuguese" in lang:
#             lang = "Portuguese"
#
#         if re.search(r"chinese.*traditional", lang, re.IGNORECASE):
#             lang = "Chinese (Traditional)"
#         elif re.search(r"chinese.*simplified", lang, re.IGNORECASE):
#             lang = "Chinese (Simplified)"
#
#         if lang in VALID_LANGUAGES:
#             cleaned_languages.append(lang)
#
#     return sorted(set(cleaned_languages))


def clean_description(raw_text: str):
    """
    Extract languages mentioned in the text (with normalization)
    and clean the remaining text for semantic searching.

    Returns:
      - cleaned_text: A string of 'cleaned' descriptions.
      - found_languages: A sorted list of unique languages mentioned.
    """

    raw_text = clean_text(raw_text)

    # -------------------------------------------------------------------------
    # 1) Extract languages using regex + synonyms mapping.
    # -------------------------------------------------------------------------

    # Define synonyms (keys are all lowercase) for normalizing different variants.
    synonyms = {
        # English
        "english": "English",
        # French
        "french": "French", "français": "French",
        # German
        "german": "German", "deutsch": "German",
        # Arabic
        "arabic": "Arabic",
        # Brazilian Portuguese / Portuguese (Brazil)
        "brazilian portuguese": "Portuguese (Brazil)",
        "portuguese (brazil)": "Portuguese (Brazil)",
        # Czech
        "czech": "Czech", "čeština": "Czech",
        # Dutch
        "dutch": "Dutch", "nederlands": "Dutch",
        # Hindi
        "hindi": "Hindi", "हिन्दी": "Hindi",
        # Italian
        "italian": "Italian", "italiano": "Italian",
        # Japanese
        "japanese": "Japanese", "japan": "Japanese", "日本": "Japanese",
        # Polish
        "polish": "Polish", "polski": "Polish",
        # Spanish
        "spanish": "Spanish", "español": "Spanish",
        # Turkish
        "turkish": "Turkish", "türkçe": "Turkish",
        # Ukrainian
        "ukrainian": "Ukrainian", "українська": "Ukrainian",
        # Chinese (Traditional)
        "traditional chinese": "Chinese (Traditional)",
        "chinese (traditional)": "Chinese (Traditional)",
        "繁體中文": "Chinese (Traditional)",
        # Chinese (Simplified) - if present
        "简体中文": "Chinese (Simplified)",
    }

    # Build a regex pattern from the synonyms keys.
    language_keys = list(synonyms.keys())
    # Sort by length (descending) to capture multi-word languages first (e.g. "brazilian portuguese").
    language_keys.sort(key=len, reverse=True)

    # Create a pattern that matches any of the language variants.
    # We use word boundaries (\b) and case-insensitive matching.
    language_pattern = re.compile(r"\b(" + "|".join(map(re.escape, language_keys)) + r")\b", flags=re.IGNORECASE)

    # Use a set to avoid duplicates.
    found_langs = set()

    # Find all occurrences
    for match in language_pattern.findall(raw_text):
        lower_match = match.lower()
        # Use synonyms to standardize
        if lower_match in synonyms:
            found_langs.add(synonyms[lower_match])
        else:
            # If not in synonyms, you can add raw or ignore it.
            found_langs.add(match)

    # -------------------------------------------------------------------------
    # 2) Clean the raw text for semantic search.
    # -------------------------------------------------------------------------

    # Split into lines
    lines = raw_text.splitlines()

    # Define boilerplate phrases or patterns to remove:
    boilerplate_keywords = [
        r"^note:",
        r"^about this learning activity",
        r"^select enroll",
        r"^select start tracking progress",
        r"^click here to",
        r"^> when you complete all courses",
        r"^did you know that every \d+ seconds a cyber attack occurs\?",
    ]
    boilerplate_pattern = re.compile("|".join(boilerplate_keywords), flags=re.IGNORECASE)

    cleaned_lines = []
    seen_lines = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove boilerplate lines
        if boilerplate_pattern.search(line):
            continue

        # Remove lines that start with "Languages:" or "Language:"
        if re.match(r"^languages?:", line, flags=re.IGNORECASE):
            continue

        # Convert to lower case for uniformity
        line = line.lower()

        # Deduplicate lines
        if line not in seen_lines:
            seen_lines.add(line)
            cleaned_lines.append(line)

    # Join cleaned lines into a single block of text
    cleaned_text = " ".join(cleaned_lines)

    # Optionally remove punctuation if you want purely alphanumeric text
    # cleaned_text = re.sub(r"[^\w\s]", "", cleaned_text)

    # Normalize multiple spaces into single spaces
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    # Sort found languages for a predictable order
    found_languages = sorted(found_langs)

    return {"description": cleaned_text, "languages": found_languages}