from pathlib import Path

from legacy.site_scraper.browser_client import FreelancerBrowserClient


def test_browser_client_keeps_configuration(tmp_path: Path) -> None:
    client = FreelancerBrowserClient(tmp_path / "profile", headless=True)

    assert client.profile_dir == tmp_path / "profile"
    assert client.headless is True
    assert client.executable_path.name == "opera.exe"


def test_import_existing_session_skips_existing_profile(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    client = FreelancerBrowserClient(profile_dir)

    client.import_existing_session()

    assert profile_dir.is_dir()


def test_browser_client_accepts_existing_browser_connection(tmp_path: Path) -> None:
    client = FreelancerBrowserClient(tmp_path / "profile", cdp_url="http://127.0.0.1:9222")

    assert client.cdp_url == "http://127.0.0.1:9222"
