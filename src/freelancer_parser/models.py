from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    title: str
    price: str
    description: str
    skills: list[str]
    url: str
    posted_at: str
