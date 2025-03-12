from bs4 import BeautifulSoup
from utils.text_utils import (
    clean_text, clean_type, clean_duration, clean_learners_amount,
    clean_star_rating, clean_star_num_ratings, clean_description, clean_tags, clean_raw_description
)

def extract_elements(
    selector, soup, single=True, unwanted_selector=None, attribute=None, clean_func=None
):
    """Extracts and cleans elements using BeautifulSoup selectors."""
    clean_func = clean_func or clean_text  # Default to general text cleaning

    def clean_element(element):
        """Cleans a single element's text or attribute value."""
        if unwanted_selector:
            for unwanted in element.select(unwanted_selector):
                unwanted.decompose()
        raw_value = element.get(attribute, None) if attribute else element.text
        return clean_func(raw_value) if clean_func else raw_value  # Apply cleaner if given

    if single:
        element = soup.select_one(selector)
        return clean_element(element) if element else None

    elements = soup.select(selector)
    return [clean_element(elem) for elem in elements] if elements else []


def parse_course_page(html_source, url, course_category):
    soup = BeautifulSoup(html_source, 'lxml')

    raw_description = extract_elements('.FullPageDescription_wrapper__CEPjU > div', soup, clean_func=clean_raw_description) or ""
    desc_result = clean_description(raw_description)

    cleaned_description = desc_result.get("description", "") if isinstance(desc_result, dict) else desc_result or ""
    languages = desc_result.get("languages", []) if isinstance(desc_result, dict) else []

    raw_tags = extract_elements('[class^="TagLabel_labelContainer__"] > span', soup, single=False) or []
    cleaned_tags = clean_tags(raw_tags)

    return {
        "course_url": url or "",
        "category": course_category,
        "type": extract_elements('#full-page-header-type', soup, clean_func=clean_type) or "",
        "title": extract_elements(
            'h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span',
            soup,
        ) or "",
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time',
            soup,
            unwanted_selector=".sr-only",
            clean_func=clean_duration
        ) or 0,
        "learners_amount": extract_elements(
            '#a11y-undefined-learners',
            soup,
            attribute='title',
            clean_func=clean_learners_amount
        ) or 0,
        "star_rating": extract_elements(
            '#a11y-undefined-rating', soup, attribute='title', clean_func=clean_star_rating
        ) or 0.0,
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup, clean_func=clean_star_num_ratings) or 0,
        "raw_description": raw_description,
        "description": cleaned_description,
        "languages": languages,
        "tags": cleaned_tags
    }
