"""Conversion of Freelancer search-result HTML into Job objects."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .models import Job


class FreelancerParser:
    CARD_SELECTORS = ".JobSearchCard-item, [data-job-card], article.job-card, fl-project-contest-card.ProjectCard"
    TITLE_SELECTORS = ".JobSearchCard-primary-heading-link, [data-job-title], .Title-text, h2 a, h3 a"
    PRICE_SELECTORS = ".JobSearchCard-primary-price, [data-job-price], .BudgetUpgradeWrapper-budget, .price"
    DESCRIPTION_SELECTORS = ".JobSearchCard-primary-description, [data-job-description], .Content, .description"
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
            description=self._description(card),
            skills=self._skills(card),
            url=urljoin(source_url, href),
            posted_at=self._posted_at(card),
        )

    @staticmethod
    def _selected_text(card: Tag, selector: str) -> str:
        element = card.select_one(selector)
        return FreelancerParser._text(element) if element else ""

    @staticmethod
    def _description(card: Tag) -> str:
        element = card.select_one(FreelancerParser.DESCRIPTION_SELECTORS)
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
        for text in card.stripped_strings:
            if re.fullmatch(r"\d+\s+(?:minute|hour|day|week|month)s?\s+ago", text):
                return text
        return ""

    @staticmethod
    def _text(element: Tag) -> str:
        return element.get_text(" ", strip=True)
