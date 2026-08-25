"""CLI entry point: fetch recent Freelancer projects via the official API.

Reads your token and skill filters from config.json by default:
    1. cp config.json config.json
    2. Fill in oauth_token (from https://accounts.freelancer.com/settings/develop)
    3. python api_main.py

CLI flags override config.json for one-off runs without editing the file.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.freelancer_parser.api_client import fetch_recent_projects
from src.freelancer_parser.config import load_config
from src.freelancer_parser.skills import resolve_skill_ids

DATA_DIR = Path("data")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch recent Freelancer projects via the official API.")
    parser.add_argument("--config", default="config.json", help="Path to config file (default: config.json).")
    parser.add_argument("--skills", nargs="+", help="Override config.json skills with these names instead.")
    parser.add_argument("--limit", type=int, help="Override config.json limit.")
    parser.add_argument("--refresh-jobs-catalog", action="store_true", help="Re-download the skill/job ID list instead of using the cache.")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 1

    limit = args.limit if args.limit is not None else config.limit

    # --skills on the CLI fully replaces config.json's skill list.
    if args.skills:
        try:
            skill_ids = list(resolve_skill_ids(args.skills, force_refresh=args.refresh_jobs_catalog).values())
        except ValueError as error:
            print(error)
            return 1
    else:
        skill_ids = list(config.known_skill_ids())
        unresolved = config.unresolved_skill_names()
        if unresolved:
            print(f"Resolving skill IDs not set in config.json: {unresolved}")
            try:
                resolved = resolve_skill_ids(unresolved, force_refresh=args.refresh_jobs_catalog)
            except ValueError as error:
                print(error)
                print("Continuing without these skills. Add their IDs to config.json to fix this permanently.")
            else:
                skill_ids.extend(resolved.values())

    print(f"Using {len(skill_ids)} skill filter(s): {skill_ids}")

    try:
        jobs = fetch_recent_projects(job_ids=skill_ids, limit=limit, token=config.oauth_token)
    except RuntimeError as error:
        print(error)
        return 1
    except Exception as error:
        print(f"API request failed: {error}")
        return 1

    DATA_DIR.mkdir(exist_ok=True)
    output = DATA_DIR / "jobs_api.json"
    output.write_text(
        json.dumps([asdict(job) for job in jobs], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Found {len(jobs)} projects.")
    print(f"Saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
