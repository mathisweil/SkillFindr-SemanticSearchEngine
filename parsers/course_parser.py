from bs4 import BeautifulSoup
from utils.text_utils import clean_text, clean_type, clean_title, clean_duration, clean_learners_amount, clean_star_rating, clean_star_num_ratings, clean_description

def extract_elements(
    selector, soup, single=True, unwanted_selector=None, attribute=None, clean_func=None
):
    clean_func = clean_func or clean_text

    if single:
        if element := soup.select_one(selector):
            if unwanted_selector:
                for unwanted_child in element.select(unwanted_selector):
                    unwanted_child.decompose()
            if attribute:
                return clean_func(element.get(attribute, 'N/A'))
            return clean_func(element.text)
        return "N/A"
    else:
        elements = soup.select(selector)
        return [
            clean_func(elem.get(attribute, 'N/A') if attribute else elem.text)
            for elem in elements
        ] if elements else []


def parse_course_page(html_source, url):
    soup = BeautifulSoup(html_source, 'lxml')

    desc_result = extract_elements(
        '.FullPageDescription_wrapper__CEPjU > div', soup, clean_func=clean_description
    )

    if isinstance(desc_result, dict):
        cleaned_description = desc_result.get("description", "")
        languages = desc_result.get("languages", [])
    else:
        cleaned_description = desc_result
        languages = []

    return {
        "course_url": url,
        "type": extract_elements('#full-page-header-type', soup, clean_func=clean_type),
        "title": extract_elements(
            'h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span',
            soup,
            clean_func=clean_title
        ),
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time',
            soup,
            unwanted_selector=".sr-only",
            clean_func=clean_duration
        ),
        "learners_amount": extract_elements(
            '#a11y-undefined-learners',
            soup,
            attribute='title',
            clean_func=clean_learners_amount
        ),
        "star_rating": extract_elements(
            '#a11y-undefined-rating', soup, attribute='title', clean_func=clean_star_rating
        ),
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup, clean_func=clean_star_num_ratings),
        "description": cleaned_description,
        "languages": languages,
        "tags": extract_elements(
            '[class^="TagLabel_labelContainer__"] > span', soup, single=False
        )
    }
