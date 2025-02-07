from bs4 import BeautifulSoup
from utils.utils import clean_text

def extract_elements(selector, soup, single=True, unwanted_selector=None, attribute=None):
    if single:
        if element := soup.select_one(selector):
            if unwanted_selector:
                for unwanted_child in element.select(unwanted_selector):
                    unwanted_child.decompose()
            if attribute:
                return clean_text(element.get(attribute, 'N/A'))
            return clean_text(element.text)
        return "N/A"
    else:
        elements = soup.select(selector)
        return [
            clean_text(elem.get(attribute, 'N/A') if attribute else elem.text)
            for elem in elements
        ] if elements else "N/A"


def parse_course_page(html_source):
    soup = BeautifulSoup(html_source, 'lxml')

    return {
        "type": extract_elements('#full-page-header-type', soup),
        "title": extract_elements(
            'h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span',
            soup
        ),
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time',
            soup,
            unwanted_selector=".sr-only"
        ),
        "learners_amount": extract_elements(
            '.LearnersAmount_learnersAmount__qttyB span[class^="ActivityFullPage_textClass__"]',
            soup
        ),
        "star_rating": extract_elements(
            '#a11y-undefined-rating', soup, attribute='title'
        ),
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup),
        "description": extract_elements(
            '.FullPageDescription_wrapper__CEPjU > div', soup
        ),
        "tags": extract_elements(
            '[class^="TagLabel_labelContainer__"] > span', soup, single=False
        )
    }
