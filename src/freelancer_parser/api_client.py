"""Fetch recent active projects directly from Freelancer's official REST API.

Requires a personal OAuth access token:
  1. Log into freelancer.com
  2. Go to https://accounts.freelancer.com/settings/develop -> Access Tokens
  3. Generate a token, then:  export FLN_OAUTH_TOKEN="your-token-here"

Docs: https://developers.freelancer.com
Uses the official SDK (`pip install freelancersdk`) if present, since it
handles the API's array-parameter encoding correctly. Falls back to a plain
`requests` call against the same documented endpoint if the SDK isn't
installed.
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from .models import Job

SEARCH_ENDPOINT = "https://www.freelancer.com/api/projects/0.1/projects/active/"


def _format_price(project: dict) -> str:
    budget = project.get("budget") or {}
    currency = (project.get("currency") or {}).get("code", "")
    minimum = budget.get("minimum")
    maximum = budget.get("maximum")
    if minimum is not None and maximum is not None:
        return f"Budget ${minimum:g} – {maximum:g} {currency}".strip()
    if minimum is not None:
        return f"Budget ${minimum:g}+ {currency}".strip()
    return ""


def _format_posted_at(project: dict) -> str:
    submitdate = project.get("time_submitted") or project.get("submitdate")
    if not submitdate:
        return ""
    posted = datetime.fromtimestamp(int(submitdate), tz=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - posted
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"{max(minutes, 0)} minutes ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hours ago"
    return f"{hours // 24} days ago"


def _project_url(project: dict) -> str:
    seo_url = project.get("seo_url") or project.get("id")
    return f"https://www.freelancer.com/projects/{seo_url}"


# Cache the live CAD rate so we only fetch it once per run
_USD_TO_CAD_RATE = None


def _get_usd_to_cad_rate() -> float:
    global _USD_TO_CAD_RATE
    if _USD_TO_CAD_RATE is None:
        try:
            response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            _USD_TO_CAD_RATE = float(response.json()["rates"]["CAD"])
        except Exception:
            _USD_TO_CAD_RATE = 1.38  # Fallback rate if network request fails
    return _USD_TO_CAD_RATE


def _format_price_cad(project: dict) -> str:
    budget = project.get("budget") or {}
    currency = project.get("currency") or {}
    minimum = budget.get("minimum")
    maximum = budget.get("maximum")

    if minimum is None:
        return ""

    # Freelancer gives exchange_rate relative to USD for ANY currency (EUR, INR, AUD, etc.)
    fx_rate_to_usd = float(currency.get("exchange_rate") or 1.0)
    usd_to_cad = _get_usd_to_cad_rate()

    def to_cad(amount: float) -> int:
        usd_amount = amount * fx_rate_to_usd
        return round(usd_amount * usd_to_cad)

    if minimum is not None and maximum is not None:
        return f"~${to_cad(minimum)} – {to_cad(maximum)} CAD"
    elif minimum is not None:
        return f"~${to_cad(minimum)}+ CAD"

    return ""


def _project_to_job(project: dict) -> Job:
    skills = [job.get("name", "") for job in (project.get("jobs") or []) if job.get("name")]
    full_desc = project.get("description") or project.get("preview_description") or ""

    # Extract bid count from API response structure
    bid_stats = project.get("bid_stats") or {}
    bid_count = int(bid_stats.get("bid_count") or project.get("bid_count") or 0)

    return Job(
        title=project.get("title", ""),
        price=_format_price(project),
        price_cad=_format_price_cad(project),
        description=full_desc.strip(),
        skills=skills,
        url=_project_url(project),
        posted_at=_format_posted_at(project),
        bids=bid_count,
    )


def _search_via_sdk(job_ids: list[int], limit: int, token: str) -> list[dict]:
    from freelancersdk.session import Session
    from freelancersdk.resources.projects.helpers import (
        create_search_projects_filter,
        create_get_projects_project_details_object,
    )
    from freelancersdk.resources.projects.projects import search_projects

    session = Session(oauth_token=token)

    # Correct SDK keyword arguments
    search_filter = create_search_projects_filter(
        jobs=job_ids or None,
        sort_field="time_submitted",
        reverse_sort=False,
        project_types=["fixed"],
        min_avg_price=30,
    )

    # Request full description explicitly
    project_details = create_get_projects_project_details_object(
        full_description=True,
        jobs=True,
    )

    result = search_projects(
        session,
        query="",
        search_filter=search_filter,
        project_details=project_details,
        limit=limit,
        offset=0,
        active_only=True,
    )
    return result.get("projects", result) if isinstance(result, dict) else result


def _search_via_raw_request(job_ids: list[int], limit: int, token: str) -> list[dict]:
    headers = {"Freelancer-OAuth-V1": token}
    params = {
        "sort_field": "time_submitted",
        "reverse_sort": "true",
        "limit": limit,
        "offset": 0,
        "compact": "false",
        "full_description": "true",
        "job_details": "true",
        "types[]": "fixed",
        "min_price": 30,
    }
    if job_ids:
        params["jobs[]"] = job_ids

    response = requests.get(SEARCH_ENDPOINT, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("result", {}).get("projects", [])


def fetch_recent_projects(job_ids: list[int], limit: int, token: str) -> list[Job]:
    """Fetch the `limit` most recently updated active projects for given job IDs."""
    try:
        raw_projects = _search_via_sdk(job_ids, limit, token)
    except ImportError:
        raw_projects = _search_via_raw_request(job_ids, limit, token)
    return [_project_to_job(project) for project in raw_projects]
