"""Conversion of Freelancer search-result HTML into Job objects."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from src.freelancer_parser.models import Job


class FreelancerParser:
    CARD_SELECTORS = ".JobSearchCard-item, [data-job-card], article.job-card, fl-project-contest-card.ProjectCard"
    TITLE_SELECTORS = ".JobSearchCard-primary-heading-link, [data-job-title], .Title-text, h2 a, h3 a"
    PRICE_SELECTORS = ".JobSearchCard-primary-price, [data-job-price], .BudgetUpgradeWrapper-budget, .price"
    DESCRIPTION_SELECTORS = (
        ".JobSearchCard-primary-description, [data-job-description], "
        "p.mb-xxsmall:not(.AverageBid-copy), .description, "
        ".ContentTextSizeSetterContainer, .Content"
    )
    SKILL_SELECTORS = ".JobSearchCard-primary-tags a, [data-job-skills] a, .SkillsWrapper-skill, .skills a"
    POSTED_AT_SELECTORS = ".JobSearchCard-primary-heading-days, [data-job-posted-at], .posted-at, time"

    def parse(self, html: str, source_url: str = "https://www.freelancer.com/") -> list[Job]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        for card in soup.select(self.CARD_SELECTORS):
            job = self._parse_card(card, source_url)
            if job is not None:
                jobs.append(job)
        return jobs

    def parse_detail_description(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(
            ".Project-description, .ProjectDescription, .LongDescription, [data-project-description]"
        )
        return self._text(element) if element else ""

    def _parse_card(self, card: Tag, source_url: str) -> Job | None:
        title_element = card.select_one(self.TITLE_SELECTORS)
        if title_element is None:
            return None
        title = self._text(title_element)
        title_link = title_element if title_element.name == "a" else title_element.find_parent("a", href=True)
        href = title_link.get("href") if title_link else None
        if not title or not href:
            return None
        return Job(
            title=title,
            price=self._selected_text(card, self.PRICE_SELECTORS),
            price_cad="",
            description=self._description(card),
            skills=self._skills(card),
            url=urljoin(source_url, href),
            posted_at=self._posted_at(card),
            bids=0,
        )

    @staticmethod
    def _first_match(card: Tag, selectors: str) -> Tag | None:
        """Try each selector in priority order; return the first that matches
        (unlike select_one on a comma-list, which returns whichever selector's
        match appears first in the DOM, not whichever selector is listed first).
        """
        for selector in selectors.split(","):
            element = card.select_one(selector.strip())
            if element is not None:
                return element
        return None

    @staticmethod
    def _selected_text(card: Tag, selector: str) -> str:
        element = FreelancerParser._first_match(card, selector)
        return FreelancerParser._text(element) if element else ""

    @staticmethod
    def _description(card: Tag) -> str:
        element = FreelancerParser._first_match(card, FreelancerParser.DESCRIPTION_SELECTORS)
        if element is None:
            return ""
        read_more = element.select_one(".ReadMoreButton")
        if read_more is not None:
            read_more.decompose()
        return FreelancerParser._text(element)

    @staticmethod
    def _skills(card: Tag) -> list[str]:
        skills: list[str] = []
        for element in card.select(FreelancerParser.SKILL_SELECTORS):
            skill = FreelancerParser._text(element)
            if skill and skill not in skills:
                skills.append(skill)
        return skills

    @staticmethod
    def _posted_at(card: Tag) -> str:
        element = card.select_one(FreelancerParser.POSTED_AT_SELECTORS)
        if element is not None:
            return str(element.get("datetime") or element.get("data-job-posted-at") or FreelancerParser._text(element))
        relative_time = card.select_one("fl-relative-time")
        if relative_time is not None and relative_time.parent is not None:
            return FreelancerParser._text(relative_time.parent)
        for text in card.stripped_strings:
            if re.fullmatch(r"\d+\s+(?:minute|hour|day|week|month)s?\s+ago", text):
                return text
        return ""

    @staticmethod
    def _text(element: Tag) -> str:
        return element.get_text(" ", strip=True)
