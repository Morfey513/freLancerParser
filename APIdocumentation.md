# Freelancer API Scraper & Parser

This document contains implementation-specific details for the current API
scraper. The API path is the primary application; the browser scraper is
retained separately under `legacy/site_scraper/`.

## Architecture

```text
api_main.py                     # API CLI and orchestration
src/freelancer_parser/
    api_client.py               # API access, filtering, conversion, CAD rates
    config.py                   # config.json and FLN_OAUTH_TOKEN handling
    skills.py                   # skill catalog lookup and caching
    models.py                   # shared Job model
data/
    jobs_api.json               # generated API output
    jobs_catalog.json           # generated skill catalog cache
```

`api_main.py` loads configuration, resolves configured skill names, fetches
recent projects, converts them to the shared `Job` model, and writes
`data/jobs_api.json`.

## Features and API behavior

- Projects are sorted newest-first by `time_submitted`.
- Results are limited to active fixed-price projects with a minimum budget
  filter of 30 USD (or the API's native-currency equivalent).
- Human-readable skill names are converted to Freelancer numeric `job_id`
  values through the public jobs catalog. The catalog parser accepts both a
  top-level list response and dictionary/wrapper responses such as
  `{"result": {"jobs": [...]}}` or `{"result": [...]}`.
- Full descriptions are requested instead of preview-only text.
- Bid metrics are read from `bid_stats.bid_count`, with `bid_count` as a
  fallback, and exposed as the integer `bids` field. Missing values become
  `0`.
- Native project budgets are converted to approximate CAD using the
  Freelancer exchange rate and a cached-per-run USD-to-CAD rate. If the
  external rate request fails, the implementation uses its built-in fallback
  rate.
- The preferred request path uses `freelancersdk`; if that package is not
  installed, the scraper falls back to direct `requests` calls against the
  same API endpoint.

## Prerequisites and installation

Python 3.10+ is required. From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install requests freelancersdk
```

`requirements.txt` declares Playwright, Beautiful Soup, and pytest. Playwright
supports the retained legacy browser scraper and its tests. `requests` is
required by the API implementation; `freelancersdk` enables the preferred SDK
request path and is optional at runtime because a raw HTTP fallback exists.

## OAuth token and configuration

1. Log into Freelancer.
2. Open the official [Freelancer Developer Applications page](https://accounts.freelancer.com/settings/develop), create a Personal Access Token, and grant the required Projects read access.

Create `config.json` in the project root:

```json
{
  "oauth_token": "YOUR_FREELANCER_OAUTH_TOKEN_HERE",
  "limit": 60,
  "skills": {
    "Python": 95,
    "HTML": 7,
    "Web Development": null
  }
}
```

Use numeric IDs for known skills. Set a skill to `null` to resolve it from the
catalog at runtime. `FLN_OAUTH_TOKEN`, when set, takes precedence over the
`oauth_token` value in `config.json`. Keep both the configuration file and the
environment token private.

## CLI usage

Default run:

```powershell
python api_main.py
```

Available major options:

```text
--config PATH                 Configuration file (default: config.json)
--skills NAME [NAME ...]      Replace configured skills for this run
--limit NUMBER                Replace the configured result limit
--refresh-jobs-catalog        Re-download the skill catalog
```

Examples:

```powershell
python api_main.py --skills "PHP" "React.js" "MySQL" --limit 20
python api_main.py --refresh-jobs-catalog
python api_main.py --config another-config.json
```

## Output structure

The API output is a JSON array in `data/jobs_api.json`. A representative entry
is:

```json
{
  "title": "Complete MEAN Stack Build",
  "price": "Budget $1500 – 12500 INR",
  "price_cad": "~$25 – 207 CAD",
  "description": "Build a full web application.",
  "skills": ["Node.js", "MongoDB", "Angular"],
  "url": "https://www.freelancer.com/projects/angular/complete-mean-stack-build",
  "posted_at": "4 minutes ago",
  "bids": 14
}
```

The skill catalog cache is written to `data/jobs_catalog.json`. Both files are
generated artifacts and are ignored by Git.

## Query parameter mapping

| Filter / concept | SDK keyword | Raw HTTP parameter | Value |
| --- | --- | --- | --- |
| Sort field | `sort_field` | `sort_field` | `time_submitted` |
| Sort direction | `reverse_sort` | `reverse_sort` | `False` / `"true"` as currently sent |
| Project type | `project_types` | `types[]` | `fixed` |
| Minimum budget | `min_avg_price` | `min_price` | `30` |
| Full details | `project_details` | `full_description` | enabled / `"true"` |
| Job filters | `jobs` | `jobs[]` | resolved numeric IDs |

The SDK path also requests job details and active projects. The raw path sends
the equivalent documented query parameters to:

```text
https://www.freelancer.com/api/projects/0.1/projects/active/
```

## Legacy browser scraper

The original browser-based scraper is not the primary implementation. It is
retained under `legacy/site_scraper/` for compatibility and reference, with
the root `main.py` acting as its backward-compatible launcher:

```powershell
python main.py "https://www.freelancer.com/search/projects/?q=python"
```

It uses Playwright with a persistent Opera profile and writes
`data/raw_page.html` and `data/jobs.json`. Its browser/session options are
available through `python main.py --help`.
