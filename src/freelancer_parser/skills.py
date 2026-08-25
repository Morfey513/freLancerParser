"""Resolve human-readable skill names to Freelancer 'job' IDs.

Freelancer's search API filters by numeric job IDs, not skill names, so we
need to look them up first. This endpoint is public (no OAuth token needed).
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

JOBS_ENDPOINT = "https://www.freelancer.com/api/projects/0.1/jobs/"
CACHE_PATH = Path("data") / "jobs_catalog.json"


def fetch_jobs_catalog(force_refresh: bool = False) -> list[dict]:
    """Return the full list of {id, name, category, ...} job/skill entries."""
    if not force_refresh and CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    response = requests.get(JOBS_ENDPOINT, timeout=30)
    response.raise_for_status()
    payload = response.json()

    # Handle top-level JSON list vs dictionary wrapper variations
    if isinstance(payload, list):
        jobs = payload
    elif isinstance(payload, dict):
        result = payload.get("result")
        if isinstance(result, dict):
            jobs = result.get("jobs", [])
        elif isinstance(result, list):
            jobs = result
        else:
            jobs = []
    else:
        jobs = []

    if not isinstance(jobs, list):
        raise ValueError(f"Unexpected jobs payload shape: {payload!r}")

    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    return jobs


def resolve_skill_ids(skill_names: list[str], force_refresh: bool = False) -> dict[str, int]:
    """Map requested skill names (case-insensitive) to their job IDs.

    Raises ValueError listing any names that couldn't be matched, so typos
    fail loudly instead of silently searching without that filter.
    """
    if not skill_names:
        return {}

    catalog = fetch_jobs_catalog(force_refresh=force_refresh)
    by_lower_name = {str(job["name"]).strip().lower(): job["id"] for job in catalog}

    resolved: dict[str, int] = {}
    missing: list[str] = []
    for name in skill_names:
        job_id = by_lower_name.get(name.strip().lower())
        if job_id is None:
            missing.append(name)
        else:
            resolved[name] = job_id

    if missing:
        raise ValueError(
            f"Could not find skill(s) on Freelancer: {missing!r}. "
            "Check exact spelling/casing against Freelancer's skill picker, "
            "or pass --refresh-jobs-catalog if the local cache is stale."
        )
    return resolved