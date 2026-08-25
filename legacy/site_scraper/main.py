"""Command-line entry point for the Freelancer search-results parser."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from legacy.site_scraper.browser_client import FreelancerBrowserClient
from legacy.site_scraper.parser import FreelancerParser

DATA_DIR = Path("data")


def build_page_urls(url: str, pages: int) -> list[str]:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    urls = []
    for page_number in range(1, pages + 1):
        page_query = query.copy()
        if page_number > 1:
            page_query["page"] = str(page_number)
        else:
            page_query.pop("page", None)
        urls.append(urlunsplit((*parts[:3], urlencode(page_query), parts.fragment)))
    return urls


def main() -> int:
    command = argparse.ArgumentParser(description="Fetch and parse a Freelancer search page.")
    command.add_argument("url", nargs="?", help="Freelancer search-results URL")
    command.add_argument("--no-raw-html", action="store_true", help="Do not save data/raw_page.html.")
    command.add_argument(
        "--login",
        action="store_true",
        help="Open Freelancer so you can log in manually and save the local browser session.",
    )
    command.add_argument("--headless", action="store_true", help="Run the browser without displaying it.")
    command.add_argument("--pages", type=int, default=1, choices=range(1, 4), help="Search-result pages to load (1-3).")
    command.add_argument("--workers", type=int, default=2, choices=range(1, 4), help="Maximum temporary Opera tabs to use.")
    command.add_argument("--full-descriptions", action="store_true", help="Expand each search card's visible 'more' control before parsing.")
    command.add_argument(
        "--reuse-opera-session",
        action="store_true",
        help="Import the existing Opera session into a separate local parser profile.",
    )
    command.add_argument(
        "--connect-existing-opera",
        action="store_true",
        help="Attach to an Opera instance started with remote debugging; do not launch another browser.",
    )
    args = command.parse_args()
    if not args.url and not args.login:
        command.error("a search-results URL is required unless --login is used")
    DATA_DIR.mkdir(exist_ok=True)
    profile_name = "opera_existing_session" if args.reuse_opera_session else "opera_profile"
    client = FreelancerBrowserClient(
        profile_dir=DATA_DIR / profile_name,
        headless=args.headless,
        cdp_url="http://127.0.0.1:9222" if args.connect_existing_opera else None,
    )
    if args.reuse_opera_session:
        try:
            client.import_existing_session()
        except Exception as error:
            print(f"Could not import the existing Opera session: {error}")
            return 1

    if args.login and args.connect_existing_opera:
        command.error("--login cannot be combined with --connect-existing-opera")
    if args.login:
        print("A browser will open. Log in manually, then return here and press Enter.")
        client.save_login_session()
        print("Saved local browser session.")
        return 0

    try:
        print("Fetching jobs...")
        search_urls = build_page_urls(args.url, args.pages)
        html_pages = client.fetch_pages(
            search_urls,
            client.result_selector(),
            args.workers,
            args.full_descriptions,
        )
    except Exception as error:
        print(f"Could not fetch the page: {error}")
        return 1

    if not args.no_raw_html:
        (DATA_DIR / "raw_page.html").write_text("\n<!-- PAGE BREAK -->\n".join(html_pages), encoding="utf-8")

    parser = FreelancerParser()
    jobs = []
    seen_urls = set()
    for page_html, page_url in zip(html_pages, search_urls):
        for job in parser.parse(page_html, source_url=page_url):
            if job.url not in seen_urls:
                jobs.append(job)
                seen_urls.add(job.url)

    output = DATA_DIR / "jobs.json"
    output.write_text(
        json.dumps([asdict(job) for job in jobs], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Found {len(jobs)} jobs.")
    print(f"Saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
