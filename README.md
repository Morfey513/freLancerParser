# Freelancer Parser

## Overview

Freelancer Parser retrieves active Freelancer.com projects and writes them as
JSON. The official API scraper is the current and primary implementation: it
is faster than browser automation and does not require an interactive browser
session.

## Quick Start

Python 3.10+ is required. Create a virtual environment and install the
declared dependencies plus the API client packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install requests freelancersdk
```

Create a private `config.json` in the project root:

```json
{
  "oauth_token": "YOUR_FREELANCER_OAUTH_TOKEN_HERE",
  "limit": 60,
  "skills": {
    "Python": 95,
    "Web Development": null
  }
}
```

To obtain a token, log into Freelancer, then open the official [Freelancer
Developer Applications page](https://accounts.freelancer.com/settings/develop),
create a Personal Access Token, and grant the required Projects read access.
The `FLN_OAUTH_TOKEN` environment variable overrides `oauth_token` in the
configuration file.

Run the API scraper:

```powershell
python api_main.py
```

Major options include one-run skill and limit overrides and skill-catalog
refreshing:

```powershell
python api_main.py --skills "PHP" "React.js" "MySQL" --limit 20
python api_main.py --refresh-jobs-catalog
```

The API output is written to `data/jobs_api.json`; the resolved skill catalog
is cached in `data/jobs_catalog.json`. Jobs include title, budgets, full
description, skills, URL, posting time, and the `bids` count. See
[APIdocumentation.md](APIdocumentation.md) for API behavior, query parameters,
payload handling, and detailed examples.

## Project Structure

```text
api_main.py                       # Primary API CLI
src/freelancer_parser/
    api_client.py                 # API access and job conversion
    config.py                     # Configuration loading
    skills.py                     # Skill resolution and catalog caching
    models.py                     # Shared Job model
legacy/site_scraper/              # Retained browser scraper
tests/                            # Automated tests
APIdocumentation.md               # Detailed API documentation
```

## Legacy Browser Scraper

The original browser-based scraper remains under `legacy/site_scraper/` for
compatibility, reference, and possible fallback use. It is not the primary
implementation. The root `main.py` command is retained only as its
backward-compatible launcher:

```powershell
python main.py "https://www.freelancer.com/search/projects/?q=python"
```

It uses a persistent Opera profile and writes legacy outputs to
`data/raw_page.html` and `data/jobs.json`. Use `python main.py --help` for its
options.

## Testing

```powershell
python -m pytest
```
