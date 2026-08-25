"""Load OAuth token and skill filters from config.json.

config.json is your personal, git-ignored copy. Never commit it — it holds
your OAuth token. config.json is the template that's safe to commit.

Precedence for the token: FLN_OAUTH_TOKEN env var (if set) wins over the
value in config.json, so CI/production can override it without editing the
file, and you don't need to touch config.json at all if you'd rather keep
the token purely in your shell environment.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config.json")
PLACEHOLDER_TOKEN = "PUT_YOUR_FREELANCER_OAUTH_TOKEN_HERE"


@dataclass(frozen=True)
class Config:
    oauth_token: str
    limit: int
    # name -> id, or name -> None if the id wasn't known and must be
    # resolved at runtime via the public /jobs endpoint.
    skills: dict[str, int | None]

    def known_skill_ids(self) -> list[int]:
        return [skill_id for skill_id in self.skills.values() if skill_id is not None]

    def unresolved_skill_names(self) -> list[str]:
        return [name for name, skill_id in self.skills.items() if skill_id is None]


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy config.json to {path} and fill in your token, "
            "or pass --config to point at a different file."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))

    token = os.environ.get("FLN_OAUTH_TOKEN") or raw.get("oauth_token", "")
    if not token or token == PLACEHOLDER_TOKEN:
        raise ValueError(
            f"No OAuth token set. Edit '{path}' and replace oauth_token with your real token "
            "(from https://accounts.freelancer.com/settings/develop), or export FLN_OAUTH_TOKEN."
        )

    return Config(
        oauth_token=token,
        limit=int(raw.get("limit", 60)),
        skills=dict(raw.get("skills", {})),
    )
