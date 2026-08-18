"""Command-line entry point for the Freelancer search-results parser."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.freelancer_parser.browser_client import FreelancerBrowserClient
from src.freelancer_parser.parser import FreelancerParser

DATA_DIR = Path("data")


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
        html = client.fetch_page(args.url)
    except Exception as error:
        print(f"Could not fetch the page: {error}")
        return 1

    if not args.no_raw_html:
        (DATA_DIR / "raw_page.html").write_text(html, encoding="utf-8")

    jobs = FreelancerParser().parse(html, source_url=args.url)
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
