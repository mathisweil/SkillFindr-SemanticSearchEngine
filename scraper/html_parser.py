from bs4 import BeautifulSoup
from typing import Any, Union, List, Dict, Optional


def extract_elements(
    selector: str,
    soup: BeautifulSoup,
    single: bool = True,
    unwanted_selector: Union[str, None] = None,
    attribute: Union[str, None] = None
) -> Union[str, List[str]]:
    """
    Extracts elements using a BeautifulSoup selector and returns their raw text or an attribute value,
    with no additional cleaning.
    """

    def get_raw(element: Any) -> str:
        if not element:
            return ""
        if unwanted_selector:
            for unwanted in element.select(unwanted_selector):
                unwanted.decompose()
        return element.get(attribute, "").strip() if attribute else element.get_text(strip=True)

    if single:
        element = soup.select_one(selector)
        return get_raw(element) if element else None
    else:
        elements = soup.select(selector)
        return [get_raw(elem) for elem in elements] if elements else []


def parse_course_page(html_source: str, url: str, course_category: str) -> Optional[Dict[str, Union[str, None, List[str]]]]:
    """
        Parses course data from HTML and returns a structured dictionary.
        Skips entries where the course URL is missing.

        Args:
            html_source: The HTML content of the page.
            url: The URL of the course (must not be None).
            course_category: The category for the course (e.g. 'cybersecurity').

        Returns:
            A dictionary of extracted course data, or None if the URL is invalid.
        """

    if not url or not url.strip():
        return None

    soup = BeautifulSoup(html_source, 'lxml')

    return {
        "course_url": url.strip(),
        "category": course_category,
        "type": extract_elements('#full-page-header-type', soup),
        "title": extract_elements('h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span', soup),
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time', soup, unwanted_selector=".sr-only"),
        "learners_amount": extract_elements('#a11y-undefined-learners', soup, attribute='title'),
        "star_rating": extract_elements('#a11y-undefined-rating', soup, attribute='title'),
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup),
        "description": extract_elements('.FullPageDescription_wrapper__CEPjU > div', soup),
        "tags": extract_elements('[class^="TagLabel_labelContainer__"] > span', soup, single=False)
    }
