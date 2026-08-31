"""Every doc exists in all six languages, and its links actually resolve.

Nothing checked this before. Adding one English page and five
translations is a routine change here, and three of the five failure
modes below were produced by that exact change:

- a translated heading with the *English* anchor still pointing at it;
- an anchor "translated" by stripping accents, when the slug GitHub
  derives keeps them (`vérifier` stays `vérifier`, not `verifier`);
- a `{#custom-id}` attribute, which GitHub Markdown does not support —
  it renders as literal text and the anchor still does not exist.

Each was reported as correct by the process that introduced it, which is
why this is a test and not a review step.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DOCS = Path(__file__).parents[1] / "docs"
LANGUAGES = ("en", "ko", "ja", "zh-Hans", "es", "fr")

_HEADING_RE = re.compile(r"^#{1,6} (.+)$", re.M)
_ANCHOR_LINK_RE = re.compile(r"\]\(#([^)]+)\)")
_RELATIVE_LINK_RE = re.compile(r"\]\((\.\./[^)#]+)")


def _slug(heading: str) -> str:
    """GitHub's heading slug: lowercase, drop punctuation, spaces to
    dashes — and keep non-ASCII letters rather than transliterating."""
    cleaned = re.sub(r"[^\w\s-]", "", heading.lower(), flags=re.UNICODE)
    return cleaned.strip().replace(" ", "-")


def _pages(language: str) -> set[str]:
    return {p.name for p in (DOCS / language).glob("*.md")}


def _all_docs() -> list[Path]:
    return sorted(p for lang in LANGUAGES for p in (DOCS / lang).glob("*.md"))


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != "en"])
def test_every_english_page_has_a_translation(language: str) -> None:
    missing = _pages("en") - _pages(language)
    assert not missing, f"docs/{language}/ is missing {sorted(missing)}"


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != "en"])
def test_no_translation_exists_without_an_english_original(language: str) -> None:
    # The English page is the source every translation is regenerated
    # from; an orphan translation silently stops tracking anything.
    orphaned = _pages(language) - _pages("en")
    assert not orphaned, f"docs/{language}/ has {sorted(orphaned)} with no English source"


@pytest.mark.parametrize("doc", _all_docs(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_in_page_anchors_match_a_real_heading(doc: Path) -> None:
    text = doc.read_text(encoding="utf-8")
    headings = {_slug(h) for h in _HEADING_RE.findall(text)}
    for anchor in _ANCHOR_LINK_RE.findall(text):
        assert anchor in headings, (
            f"{doc.parent.name}/{doc.name}: '#{anchor}' matches no heading. "
            f"Headings slugify to: {sorted(headings)}"
        )


@pytest.mark.parametrize("doc", _all_docs(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_no_unsupported_heading_id_attributes(doc: Path) -> None:
    # `## Heading {#custom-id}` is a Kramdown/Pandoc extension. GitHub
    # renders the braces as visible text and creates no such anchor.
    for heading in _HEADING_RE.findall(doc.read_text(encoding="utf-8")):
        assert "{#" not in heading, (
            f"{doc.parent.name}/{doc.name}: heading carries an unsupported "
            f"id attribute: {heading!r}"
        )


@pytest.mark.parametrize("doc", _all_docs(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_cross_language_links_point_at_files_that_exist(doc: Path) -> None:
    # The language-switcher line at the top of every page is five of
    # these, and a typo in one is invisible until somebody clicks it.
    for target in _RELATIVE_LINK_RE.findall(doc.read_text(encoding="utf-8")):
        assert (doc.parent / target).resolve().is_file(), (
            f"{doc.parent.name}/{doc.name}: '{target}' does not exist"
        )


@pytest.mark.parametrize("doc", _all_docs(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_the_language_switcher_bolds_exactly_its_own_language(doc: Path) -> None:
    header = doc.read_text(encoding="utf-8").split("\n\n", 2)[1]
    bolded = re.findall(r"\*\*([^*]+)\*\*", header)
    assert len(bolded) == 1, (
        f"{doc.parent.name}/{doc.name}: switcher bolds {bolded}, expected exactly one"
    )
    assert f"../{doc.parent.name}/" not in header, (
        f"{doc.parent.name}/{doc.name}: switcher links to its own language"
    )
