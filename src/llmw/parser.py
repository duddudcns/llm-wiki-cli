"""Deterministic Markdown parsing: frontmatter, headings, wikilinks,
markdown links, tags/aliases, and section extraction (summary/key points).

No AI/model calls happen here — everything is regex/rule based so it is
fully unit-testable and reproducible.
"""

from __future__ import annotations

import datetime
import hashlib
import re
import urllib.parse
from pathlib import Path

from llmw.frontmatter import split_frontmatter
from llmw.models import ExternalLinkRef, Heading, LinkRef, Page

# --- masking: hide fenced code / inline code / HTML comments from link and
# heading scanners, while preserving text length and newlines so downstream
# character offsets stay valid against the original body. ---

_FENCE_RE = re.compile(
    r"(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})[^\n]*\n"
    r"(?P<body>(?:.*\n)*?)"
    r"(?P=indent)(?P=fence)[ \t]*(?=\n|\Z)"
)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(`+)([^\n]*?)\1")


def _blank(match: re.Match) -> str:
    return "".join(ch if ch == "\n" else " " for ch in match.group(0))


def _mask_matches(text: str, pattern: re.Pattern) -> str:
    return pattern.sub(_blank, text)


def mask_non_prose(text: str) -> str:
    """Blank out fenced code blocks, inline code spans, and HTML comments.

    Length and newline positions are preserved so callers can still slice
    the *original* text using offsets computed against the masked text.
    """
    text = _mask_matches(text, _FENCE_RE)
    text = _mask_matches(text, _COMMENT_RE)
    text = _mask_matches(text, _INLINE_CODE_RE)
    return text


# --- headings ---

_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<text>.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9\s-]")


def _slugify(text: str) -> str:
    s = text.strip().lower()
    s = _SLUG_STRIP_RE.sub("", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s or "section"


def extract_headings(masked_body: str) -> list[Heading]:
    headings = []
    for m in _HEADING_RE.finditer(masked_body):
        text = m.group("text").strip()
        headings.append(
            Heading(level=len(m.group("hashes")), text=text, slug=_slugify(text))
        )
    return headings


# --- section extraction (used for summary / key points, on ORIGINAL text) ---


def _find_section_span(masked_body: str, heading_name: str) -> tuple[int, int] | None:
    matches = list(_HEADING_RE.finditer(masked_body))
    for i, m in enumerate(matches):
        if m.group("text").strip().lower() == heading_name.lower():
            level = len(m.group("hashes"))
            start = m.end()
            end = len(masked_body)
            for later in matches[i + 1 :]:
                if len(later.group("hashes")) <= level:
                    end = later.start()
                    break
            return start, end
    return None


def extract_section_text(original_body: str, masked_body: str, heading_name: str) -> str | None:
    span = _find_section_span(masked_body, heading_name)
    if span is None:
        return None
    start, end = span
    text = original_body[start:end].strip()
    return text or None


_BULLET_START_RE = re.compile(r"^[ \t]*[-*][ \t]+(.+?)[ \t]*$")


def extract_key_points(
    original_body: str, masked_body: str, heading_name: str = "key points"
) -> list[str]:
    """Bullet items under `heading_name`, with soft-wrapped continuation
    lines joined back onto the bullet they belong to."""
    section = extract_section_text(original_body, masked_body, heading_name)
    if not section:
        return []

    points: list[str] = []
    for raw_line in section.splitlines():
        m = _BULLET_START_RE.match(raw_line)
        if m:
            points.append(m.group(1).strip())
        elif raw_line.strip() and points:
            points[-1] = f"{points[-1]} {raw_line.strip()}"
    return points


_SUMMARY_HEADING_NAMES = ("summary", "agent summary")


def extract_summary(frontmatter: dict, original_body: str, masked_body: str) -> str | None:
    fm_summary = frontmatter.get("summary")
    if isinstance(fm_summary, str) and fm_summary.strip():
        return fm_summary.strip()
    for heading_name in _SUMMARY_HEADING_NAMES:
        section = extract_section_text(original_body, masked_body, heading_name)
        # `llmw ingest` leaves a "TODO: ..." placeholder under "## Agent
        # summary" — that's explicitly *not* a summary yet, and lint's
        # pages_without_summary check should keep flagging it until the
        # agent replaces it with real content.
        if section and not section.lower().startswith("todo"):
            return section
    return None


# --- wikilinks: [[Page]], [[Page|Alias]], [[Page#Heading]],
# [[Page#Heading|Alias]], [[#Heading]], ![[Embed]] ---

_WIKILINK_RE = re.compile(
    r"(?P<embed>!)?\[\[(?P<target>[^\]|#]*)(?:#(?P<heading>[^\]|]*))?(?:\|(?P<alias>[^\]]*))?\]\]"
)


def extract_wikilinks(masked_body: str) -> list[LinkRef]:
    links = []
    for m in _WIKILINK_RE.finditer(masked_body):
        heading = m.group("heading")
        alias = m.group("alias")
        links.append(
            LinkRef(
                target_raw=(m.group("target") or "").strip(),
                kind="embed" if m.group("embed") else "wikilink",
                target_heading=heading.strip() if heading else None,
                link_text=alias.strip() if alias else None,
            )
        )
    return links


# --- markdown links: [text](url) -> local .md edges vs external ---

_MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


def extract_markdown_links(masked_body: str) -> tuple[list[LinkRef], list[ExternalLinkRef]]:
    md_links: list[LinkRef] = []
    external_links: list[ExternalLinkRef] = []
    for m in _MD_LINK_RE.finditer(masked_body):
        text = m.group(1).strip()
        url = m.group(2).strip()
        if _SCHEME_RE.match(url) or url.startswith("//"):
            external_links.append(ExternalLinkRef(url=url, text=text or None))
            continue
        path_part, _, heading_part = url.partition("#")
        path_part = path_part.split("?", 1)[0]
        # Obsidian/GitHub-style exporters URL-encode spaces and unicode in
        # relative links (e.g. "Project%20Profile.md") — decode before we
        # try to match it against an on-disk page path.
        path_part = urllib.parse.unquote(path_part)
        heading_part = urllib.parse.unquote(heading_part) if heading_part else heading_part
        if path_part.endswith(".md"):
            md_links.append(
                LinkRef(
                    target_raw=path_part,
                    kind="mdlink",
                    target_heading=heading_part or None,
                    link_text=text or None,
                )
            )
    return md_links, external_links


# --- `related:` frontmatter — some wikis treat this list as the
# authoritative cross-reference instead of (or alongside) inline
# wikilinks. Resolved the same way wikilinks are, just tagged distinctly.
#
# Obsidian's own Properties panel writes list-of-links entries as the
# literal wikilink text (e.g. `related: ["[[Note]]"]`) when you pick a
# link through its UI, rather than a bare path/title — so a `related:`
# entry may be either form and both must resolve. ---

_BARE_WIKILINK_RE = re.compile(
    r"^!?\[\[(?P<target>[^\]|#]*)(?:#(?P<heading>[^\]|]*))?(?:\|(?P<alias>[^\]]*))?\]\]$"
)


def extract_related_links(frontmatter: dict) -> list[LinkRef]:
    links = []
    for raw in _normalize_str_list(frontmatter.get("related")):
        raw = raw.strip()
        if not raw:
            continue
        m = _BARE_WIKILINK_RE.match(raw)
        if m is None:
            links.append(LinkRef(target_raw=raw, kind="related"))
            continue
        heading = m.group("heading")
        alias = m.group("alias")
        links.append(
            LinkRef(
                target_raw=(m.group("target") or "").strip(),
                kind="related",
                target_heading=heading.strip() if heading else None,
                link_text=alias.strip() if alias else None,
            )
        )
    return links


# --- frontmatter field normalization ---


def _to_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return str(value)


def _normalize_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


# --- top level ---


def parse_page(text: str, path: str) -> Page:
    """Parse the full text of a wiki page. `path` is project-root-relative
    (POSIX-style), used only as a title fallback and not read from disk.
    """
    frontmatter, body = split_frontmatter(text)
    masked = mask_non_prose(body)

    headings = extract_headings(masked)
    wikilinks = extract_wikilinks(masked)
    md_links, external_links = extract_markdown_links(masked)
    related_links = extract_related_links(frontmatter)

    title = frontmatter.get("title")
    if not title:
        first_h1 = next((h.text for h in headings if h.level == 1), None)
        title = first_h1 or Path(path).stem
    title = str(title)

    return Page(
        path=path,
        title=title,
        body=body,
        raw_text=text,
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        mtime=0.0,
        frontmatter=frontmatter,
        type=_to_str(frontmatter.get("type")),
        status=_to_str(frontmatter.get("status")),
        summary=extract_summary(frontmatter, body, masked),
        created=_to_str(frontmatter.get("created")),
        updated=_to_str(frontmatter.get("updated") or frontmatter.get("last_updated")),
        aliases=_normalize_str_list(frontmatter.get("aliases")),
        tags=_normalize_str_list(frontmatter.get("tags")),
        headings=headings,
        links=[*wikilinks, *md_links, *related_links],
        external_links=external_links,
    )
