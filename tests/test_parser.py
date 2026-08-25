from pathlib import Path

from legacy.site_scraper.parser import FreelancerParser


FIXTURE = Path(__file__).parent / "fixtures" / "freelancer_search.html"


def test_parser_extracts_multiple_jobs() -> None:
    jobs = FreelancerParser().parse(FIXTURE.read_text(encoding="utf-8"))

    assert len(jobs) == 3
    assert jobs[0].title == "Python automation script"
    assert jobs[0].price == "$50 - $100 USD"
    assert jobs[0].description == "Automate a daily reporting workflow."
    assert jobs[0].skills == ["Python", "Automation"]
    assert jobs[0].url == "https://www.freelancer.com/projects/python/python-automation-script/"
    assert jobs[0].posted_at == "2026-08-18T09:30:00Z"


def test_parser_keeps_jobs_with_missing_optional_fields() -> None:
    job = FreelancerParser().parse(FIXTURE.read_text(encoding="utf-8"))[1]

    assert job.title == "Data cleaning"
    assert job.price == ""
    assert job.skills == []
    assert job.posted_at == ""


def test_parser_extracts_current_logged_in_search_cards() -> None:
    job = FreelancerParser().parse(FIXTURE.read_text(encoding="utf-8"))[2]

    assert job.title == "Current Freelancer project"
    assert job.price == "Budget $250 – 750 USD"
    assert job.description == "Current visible project text."
    assert job.skills == ["Python", "FastAPI"]
    assert job.url == "https://www.freelancer.com/projects/python/current-project"
    assert job.posted_at == "7 minutes ago"


def test_parser_returns_no_jobs_for_empty_page() -> None:
    assert FreelancerParser().parse("<html><body></body></html>") == []


def test_parser_extracts_full_description_from_detail_page() -> None:
    html = "<section class='ProjectDescription'>First paragraph. <p>Second paragraph.</p></section>"
    assert FreelancerParser().parse_detail_description(html) == "First paragraph. Second paragraph."
