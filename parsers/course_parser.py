from bs4 import BeautifulSoup


def extract_elements(
        selector,
        soup,
        single=True,
        unwanted_selector=None,
        attribute=None
):
    """
    Extracts elements using a BeautifulSoup selector and returns their raw text or an attribute value,
    with no additional cleaning.
    """

    def get_raw(element):
        if unwanted_selector:
            for unwanted in element.select(unwanted_selector):
                unwanted.decompose()

        if attribute:
            return element.get(attribute, None)
        else:
            return element.text

    if single:
        element = soup.select_one(selector)
        return get_raw(element) if element else ""
    else:
        elements = soup.select(selector)
        return [get_raw(elem) for elem in elements] if elements else []


def parse_course_page(html_source, url, course_category):
    soup = BeautifulSoup(html_source, 'lxml')

    return {
        "course_url": url or "",
        "category": course_category,
        "type": extract_elements('#full-page-header-type', soup) or "",
        "title": extract_elements('h1.FullPageHeader_fullPageHeader__title__DmVZ\\+ > span', soup) or "",
        "duration": extract_elements(
            '#a11y-undefined-duration, #a11y-undefined-time', soup, unwanted_selector=".sr-only") or 0,
        "learners_amount": extract_elements('#a11y-undefined-learners', soup, attribute='title') or 0,
        "star_rating": extract_elements('#a11y-undefined-rating', soup, attribute='title') or 0.0,
        "star_num_ratings": extract_elements('.Stars_numRatings__us9ns', soup) or 0,
        "description": extract_elements('.FullPageDescription_wrapper__CEPjU > div', soup),
        "tags": extract_elements('[class^="TagLabel_labelContainer__"] > span', soup, single=False)
    }
