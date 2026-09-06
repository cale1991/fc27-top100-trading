from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


@dataclass(frozen=True, slots=True)
class PersonaPreflight:
    original: str
    rewritten: str
    flags: list[str]
    approved: bool


def load_persona_config(path: str | Path = "config/persona.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def anti_slop_preflight(text: str, config: dict | None = None) -> PersonaPreflight:
    cfg = config or load_persona_config()
    anti = cfg["anti_slop"]
    rewritten = text.strip()
    flags: list[str] = []

    for phrase in anti.get("banned_phrases", []):
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(rewritten):
            flags.append(f"canned_phrase:{phrase}")
            rewritten = pattern.sub("", rewritten)

    # Remove markdown-heading spam from social drafts while preserving the words.
    lines = rewritten.splitlines()
    heading_count = sum(1 for line in lines if line.lstrip().startswith("#"))
    if heading_count > int(anti.get("max_heading_count", 1)):
        flags.append("excessive_headings")
        lines = [re.sub(r"^\s*#+\s*", "", line) for line in lines]
    rewritten = "\n".join(lines)

    engagement_patterns = [
        r"(?i)\b(like and (?:share|retweet))\b",
        r"(?i)\b(smash (?:that )?like)\b",
        r"(?i)\b(follow for more)\b",
    ]
    if anti.get("reject_engagement_bait", True):
        for pattern in engagement_patterns:
            if re.search(pattern, rewritten):
                flags.append("engagement_bait")
                rewritten = re.sub(pattern, "", rewritten)

    # Collapse obvious repeated emoji runs without removing normal single emoji usage.
    rewritten2 = re.sub(r"([^\w\s])\1{2,}", r"\1", rewritten)
    if rewritten2 != rewritten:
        flags.append("repetitive_symbol_or_emoji_pattern")
        rewritten = rewritten2

    rewritten = re.sub(r"[ \t]{2,}", " ", rewritten)
    rewritten = re.sub(r"\n{3,}", "\n\n", rewritten).strip()
    return PersonaPreflight(original=text, rewritten=rewritten, flags=flags, approved=True)
