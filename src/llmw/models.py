"""Data models shared across the parser, indexer, search, and graph modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    slug: str


@dataclass(frozen=True)
class LinkRef:
    target_raw: str
    kind: str  # "wikilink" | "embed" | "mdlink"
    target_heading: str | None = None
    link_text: str | None = None


@dataclass(frozen=True)
class ExternalLinkRef:
    url: str
    text: str | None = None


@dataclass
class Page:
    path: str  # POSIX path relative to project root, e.g. "wiki/concepts/foo.md"
    title: str
    body: str
    raw_text: str
    content_hash: str
    mtime: float
    frontmatter: dict = field(default_factory=dict)
    type: str | None = None
    status: str | None = None
    summary: str | None = None
    created: str | None = None
    updated: str | None = None
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    links: list[LinkRef] = field(default_factory=list)
    external_links: list[ExternalLinkRef] = field(default_factory=list)
