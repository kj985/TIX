"""Works out which project (band) a gig belongs to from its text."""
import re
from dataclasses import dataclass

from .config import Project

# Where a keyword was found, and how much that counts.
FIELD_WEIGHTS = {"title": 3, "lineup": 2, "description": 1}


@dataclass
class Detection:
    project: str | None
    reason: str


def normalise(text: str) -> str:
    """Lowercase, treat & and + as 'and', drop punctuation, squash spaces."""
    text = text.lower().replace("&", " and ").replace("+", " and ")
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def _contains(haystack: str, keyword: str) -> bool:
    # Whole-word match, so "solo" doesn't match "solomon".
    return f" {keyword} " in f" {haystack} "


def detect_project(
    title: str | None,
    lineup: list[str],
    description: str | None,
    projects: list[Project],
    fallback: str | None,
) -> Detection:
    fields = {
        "title": [normalise(title or "")],
        "lineup": [normalise(name) for name in lineup],
        "description": [normalise(description or "")],
    }

    best: tuple[int, Project, list[str]] | None = None
    for project in projects:
        score = 0
        hits = []
        for field_name, texts in fields.items():
            for keyword in project.keywords:
                kw = normalise(keyword)
                if kw and any(_contains(t, kw) for t in texts):
                    score += FIELD_WEIGHTS[field_name]
                    hits.append(f'"{keyword}" in {field_name}')
                    break  # one hit per field is enough
        if score and (best is None or score > best[0]):
            best = (score, project, hits)

    if best:
        return Detection(best[1].name, "Matched " + ", ".join(best[2]))
    if fallback:
        return Detection(fallback, "No keywords matched, so used the default project")
    return Detection(None, "No keywords matched")
