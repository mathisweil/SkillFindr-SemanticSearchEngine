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


def clean_description(description):
    """
    Cleans the 'description' field by applying general cleaning
    and additional domain-specific rules.

    For example, if the description begins with boilerplate phrases such as
    "About this learning activity", these are removed to improve the signal
    for semantic search.

    Args:
        description (str): The course description text.

    Returns:
        str: The cleaned description.
    """
    description = clean_text(description)
    # Remove a common boilerplate prefix, if present
    description = re.sub(r'^(About this learning activity\s*)', '', description, flags=re.IGNORECASE)
    return description
