"""Backward-compatible entry point for the legacy browser scraper."""
from __future__ import annotations

from legacy.site_scraper.main import main


if __name__ == "__main__":
    raise SystemExit(main())
