import re


def clean_text(text):
    """
    General text cleaning function.

    This function performs basic cleaning on the input text:
      - Strips leading and trailing whitespace.
      - Normalises internal whitespace (e.g. multiple spaces or line breaks).

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    if not isinstance(text, str):
        return text
    # Remove leading/trailing whitespace and normalise spaces
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def clean_type(type_text):
    return type_text.strip().lower().replace(' ', '_') if type_text else "N/A"


def clean_title(title_text):
    return " ".join(title_text.strip().split()) if title_text else "N/A"


def clean_duration(duration_text):
    """
    Cleans the duration field by extracting hours and minutes from a text string.

    Args:
        duration_text (str): The duration text (e.g. "6 hrs", "7 hours 30 mins").

    Returns:
        str: A string in the format "HH:MM".
    """
    if not duration_text:
        return "00:00"

    # Match hours using a non-capturing group for the unit part.
    hours_match = re.search(r'(\d+)\s*(?:hrs?|hours?)', duration_text, re.IGNORECASE)
    hours = int(hours_match[1]) if hours_match else 0

    # Match minutes using a non-capturing group for the unit part.
    minutes_match = re.search(r'(\d+)\s*(?:mins?|minutes?)', duration_text, re.IGNORECASE)
    minutes = int(minutes_match[1]) if minutes_match else 0

    # Return formatted HH:MM
    return f"{hours:02}:{minutes:02}"


def clean_learners_amount(learners_amount):
    """
    Cleans the 'learners_amount' field by extracting the first numeric value
    from the provided text and converting it to an integer.

    For example, the input "29,442" becomes 29442, and 
    "29451 learners have completed this activity in the past 12 months." 
    becomes 29451. If the field is "N/A" or no number is found, None is returned.

    Args:
        learners_amount (str): The learners amount as a string.

    Returns:
        int or None: The numeric learners amount or None if not available.
    """
    if not isinstance(learners_amount, str):
        return learners_amount
    if learners_amount.strip().upper() == "N/A":
        return None

    if match := re.search(r'\d[\d,]*', learners_amount):
        # Remove commas from the matched numeric string before conversion.
        numeric_str = match.group().replace(',', '')
        return int(numeric_str)
    return None


def clean_star_rating(star_rating):
    """
    Extracts the numeric star rating from a descriptive string.

    For instance, from an input such as:
      "Average rating of 4.5 stars by 1960 learners in the past 12 months."
    this function extracts and returns the float value 4.5.

    Args:
        star_rating (str): The star rating description.

    Returns:
        float or original value: The extracted rating as a float if found,
        otherwise the original value.
    """
    if not isinstance(star_rating, str):
        return star_rating
    match = re.search(r'([0-9]*\.?[0-9]+)', star_rating)
    return float(match[1]) if match else star_rating


def clean_star_num_ratings(star_num_ratings):
    """
    Cleans the 'star_num_ratings' field by removing extraneous characters
    and converting the result to an integer.

    Args:
        star_num_ratings (str): The star number ratings as a string.

    Returns:
        int or None: The numeric count of ratings or None if not available.
    """
    if not isinstance(star_num_ratings, str):
        return star_num_ratings
    if star_num_ratings.strip().upper() == "N/A":
        return None
    digits = re.sub(r'\D', '', star_num_ratings)
    return int(digits) if digits else None


def clean_description(description_text):
    """
    Cleans the description field and extracts language information if specified.

    This function:
      - Normalises whitespace.
      - Removes boilerplate prefixes such as "About this learning activity".
      - First, searches for a "Note:" segment that includes a language list.
      - If found, only the languages from that segment are extracted.
      - Otherwise, falls back to searching for explicit markers (e.g. "Languages:" or "available in ...").
      - Removes the language segments from the description.
      - Optionally strips trailing instructional text.

    Args:
        description_text (str): The original description text.

    Returns:
        dict: A dictionary with:
              - "description": the cleaned description text.
              - "languages": a list of extracted languages.
    """
    if not description_text or not isinstance(description_text, str):
        return {"description": "", "languages": []}

    cleaned_text = re.sub(r'\s+', ' ', description_text).strip()

    cleaned_text = re.sub(r'(?i)^About this learning activity\s*', '', cleaned_text)

    languages_found = []

    note_pattern = re.compile(r'(?i)Note:\s*.*?available in\s*([^.]+)\.', re.DOTALL)
    note_match = note_pattern.search(cleaned_text)
    if note_match:
        languages_found.append(note_match[1])
        cleaned_text = note_pattern.sub('', cleaned_text)
    else:
        pattern1 = re.compile(r'(?i)(Languages?:)\s*([^.]+)')
        pattern2 = re.compile(r'(?i)available in (?:these languages here:\s*)?([^.]+)')
        for pattern in [pattern1, pattern2]:
            matches = pattern.findall(cleaned_text)
            for match in matches:
                if isinstance(match, tuple):
                    languages_found.append(match[1])
                else:
                    languages_found.append(match)
            cleaned_text = pattern.sub('', cleaned_text)

    cleaned_text = re.sub(
        r'(?i)A version of this course is available in these languages here:.*?Description',
        '',
        cleaned_text
    )

    cleaned_text = re.sub(r'(?i)Language:\s*[^.]+(\.|$)', '', cleaned_text)

    languages_list = []
    for lang_str in languages_found:
        lang_str = re.sub(r'\s+and\s+', ', ', lang_str, flags=re.IGNORECASE)
        parts = [l.strip() for l in lang_str.split(',') if l.strip()]
        languages_list.extend(parts)

    languages_list = sorted(set(languages_list))

    cleaned_text = re.sub(r'(?i)Select Enroll.*$', '', cleaned_text).strip()

    return {"description": cleaned_text, "languages": languages_list}
