import re
import html
import unicodedata
import codecs
from typing import Any

import ftfy
import langcodes
from bs4 import BeautifulSoup

from config.config import load_config, load_boilerplate_phrases


class DescriptionCleaner:
    """
    Clean an HTML course-description:
      - strip unwanted tags
      - decode & normalise text
      - remove URLs, numeric garbage, durations & boilerplate
      - extract language codes
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if config is None:
            config = load_config()
        phrases = load_boilerplate_phrases()

        self.boilerplate_pattern = self._compile_phrases_pattern(phrases)
        self.duration_pattern = re.compile(
            r"(?:duration|expected duration)\s*:\s*"
            r"(complete the activities.*?learning credit!|"
            r"(?:this course will take you about\s*)?\d+\s*"
            r"(?:hours?|hrs?|h|minutes?|mins?|m)"
            r"(?:,\s*\d+\s*(?:minutes?|mins?|m))?)",
            flags=re.IGNORECASE,
        )
        self.language_span_pattern = re.compile(
            r"(?:languages\s*:|available in|here\s*:|"
            r"a version of this course is available in)\s*"
            r"((?:[^.:;\n]|[ -￿])+)",
            flags=re.IGNORECASE,
        )
        self.learners_pattern = re.compile(
            r"(?:\b[a-z]+\s+)?learners?\s+can\s+complete\s+the\s+learning"
            r"(?:\s+here:)?",
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _compile_phrases_pattern(phrases: list[str]) -> re.Pattern:
        """
        Build a single regex that matches any of the boilerplate phrases,
        allowing for trailing punctuation or ellipses.
        """
        escaped = (re.escape(p) for p in phrases)
        pattern = r"|".join(rf"\s*{p}[\s\.,;:!?\u2026\u3002]*" for p in escaped)
        return re.compile(pattern, flags=re.IGNORECASE)

    @staticmethod
    def _extract_languages_from_soup(soup: BeautifulSoup) -> list[str]:
        langs = set()
        for tag in soup.find_all(attrs={"lang": True}):
            val = tag.get("lang", "").strip()
            if not val:
                continue
            try:
                lc = langcodes.get(val)
                langs.add(lc.language.lower() if lc and lc.language else val.lower())
            except Exception:
                langs.add(val.lower())
        return list(langs)

    @staticmethod
    def _extract_iso_languages(text: str) -> tuple[str, list[str]]:
        """
        Pull out any named languages (e.g. "English, Français") and return
        (text_without_those_mentions, [iso_codes…])
        """
        candidates = [
            c.strip(" .;:,")
            for c in re.split(r",|\band\b", text)
            if c.strip()
        ]
        iso_codes = set()
        modified = text
        for cand in candidates:
            try:
                lc = langcodes.find(cand)
                if lc and lc.language:
                    iso_codes.add(lc.language.lower())
                    # remove that chunk from the text
                    modified = re.sub(
                        rf"\b{re.escape(cand)}\b",
                        "",
                        modified,
                        flags=re.IGNORECASE,
                    )
            except Exception:
                continue

        return re.sub(r"\s+", " ", modified).strip(), list(iso_codes)

    def clean(self, raw_html: str) -> tuple[str, list[str]]:
        """
        Returns a tuple (clean_text, [language_codes…]).
        """
        if not isinstance(raw_html, str):
            return raw_html, []

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript"]):
            tag.decompose()

        html_langs = self._extract_languages_from_soup(soup)

        text = soup.get_text()
        text = html.unescape(text).lower()

        text, text_langs = self._extract_iso_languages(text)

        try:
            text = codecs.decode(text, "unicode_escape")
        except Exception:
            pass
        text = unicodedata.normalize("NFKC", text)
        text = ftfy.fix_text(text)
        text = ftfy.fix_encoding(text)
        text = re.sub(r"[\u2020\u0304\u00a0]+", " ", text)

        text = re.sub(r"http\S+|www\.\S+", "", text)
        text = re.sub(r"\d{5,}", "", text)

        for pattern in (
            self.language_span_pattern,
            self.duration_pattern,
            self.boilerplate_pattern,
            self.learners_pattern,
        ):
            text = pattern.sub(" ", text)

        langs = set(html_langs) | set(text_langs)
        if not langs:
            langs.add("en")

        text = re.sub(r"([,.!?;:])\1+", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text, list(langs)
