import pytest

from llmw.frontmatter import InvalidFrontmatterError, split_frontmatter
from llmw.parser import (
    extract_key_points,
    extract_markdown_links,
    extract_related_links,
    extract_summary,
    extract_wikilinks,
    mask_non_prose,
    parse_page,
)


def test_split_frontmatter_basic():
    text = "---\ntitle: Test Page\ntags:\n  - test\n---\n\n# Body\n"
    fm, body = split_frontmatter(text)
    assert fm == {"title": "Test Page", "tags": ["test"]}
    assert body == "\n# Body\n"


def test_split_frontmatter_absent_returns_empty_dict():
    fm, body = split_frontmatter("# Just a body\n")
    assert fm == {}
    assert body == "# Just a body\n"


def test_split_frontmatter_invalid_yaml_raises():
    text = "---\ntitle: [unterminated\n---\nbody\n"
    with pytest.raises(InvalidFrontmatterError):
        split_frontmatter(text)


def test_split_frontmatter_non_mapping_raises():
    text = "---\n- a\n- b\n---\nbody\n"
    with pytest.raises(InvalidFrontmatterError):
        split_frontmatter(text)


WIKILINK_FIXTURE = """\
# A

Links: [[B]], [[C|see C]], [[D#Part|D part]], ![[E]], [[#Heading]]

```text
[[Ignored]]
```

Inline `[[Code Inline]]` should not parse.
"""


def test_wikilink_parsing_matches_acceptance_fixture():
    masked = mask_non_prose(WIKILINK_FIXTURE)
    links = extract_wikilinks(masked)
    targets = [(link.kind, link.target_raw, link.target_heading, link.link_text) for link in links]

    assert ("wikilink", "B", None, None) in targets
    assert ("wikilink", "C", None, "see C") in targets
    assert ("wikilink", "D", "Part", "D part") in targets
    assert ("embed", "E", None, None) in targets
    assert ("wikilink", "", "Heading", None) in targets

    all_raw_targets = [t[1] for t in targets]
    assert "Ignored" not in all_raw_targets
    assert "Code Inline" not in all_raw_targets
    assert len(targets) == 5


def test_html_comment_is_masked():
    text = "Before <!-- [[Hidden]] --> after [[Visible]]"
    masked = mask_non_prose(text)
    links = extract_wikilinks(masked)
    raw_targets = [link.target_raw for link in links]
    assert raw_targets == ["Visible"]


def test_markdown_link_classifies_local_md_vs_external():
    text = (
        "See [Some Page](concepts/some-page.md) and "
        "[Heading Link](concepts/other.md#some-heading) and "
        "[External](https://example.com) and "
        "![ignored image](assets/pic.png)"
    )
    masked = mask_non_prose(text)
    md_links, external_links = extract_markdown_links(masked)

    assert len(md_links) == 2
    assert md_links[0].target_raw == "concepts/some-page.md"
    assert md_links[0].target_heading is None
    assert md_links[1].target_raw == "concepts/other.md"
    assert md_links[1].target_heading == "some-heading"

    assert len(external_links) == 1
    assert external_links[0].url == "https://example.com"


def test_parse_page_title_fallback_order():
    with_fm_title = parse_page(
        "---\ntitle: FM Title\n---\n# H1 Title\n", "wiki/concepts/foo.md"
    )
    assert with_fm_title.title == "FM Title"

    with_h1_only = parse_page("# H1 Title\n\nbody\n", "wiki/concepts/foo.md")
    assert with_h1_only.title == "H1 Title"

    with_neither = parse_page("no heading here\n", "wiki/concepts/my-page.md")
    assert with_neither.title == "my-page"


def test_parse_page_normalizes_tags_and_aliases():
    text = (
        "---\n"
        "title: T\n"
        "tags: solo-tag\n"
        "aliases:\n  - A1\n  - A2\n"
        "---\n"
        "body\n"
    )
    page = parse_page(text, "wiki/concepts/t.md")
    assert page.tags == ["solo-tag"]
    assert page.aliases == ["A1", "A2"]


def test_parse_page_stringifies_yaml_dates():
    text = "---\ntitle: T\ncreated: 2026-07-03\nupdated: 2026-07-03\n---\nbody\n"
    page = parse_page(text, "wiki/concepts/t.md")
    assert page.created == "2026-07-03"
    assert page.updated == "2026-07-03"


def test_extract_summary_prefers_frontmatter_then_section():
    fm_only = parse_page("---\nsummary: From frontmatter\n---\nbody\n", "p.md")
    assert fm_only.summary == "From frontmatter"

    section_only_text = "# P\n\n## Summary\n\nFrom section body.\n\n## Related\n\nx\n"
    section_only = parse_page(section_only_text, "p.md")
    assert section_only.summary == "From section body."

    none_present = parse_page("# P\n\nplain text\n", "p.md")
    assert none_present.summary is None


def test_extract_key_points():
    body = "# P\n\n## Key points\n\n- point one\n- point two\n\n## Related\n\nx\n"
    masked = mask_non_prose(body)
    points = extract_key_points(body, masked)
    assert points == ["point one", "point two"]


def test_extract_key_points_joins_wrapped_continuation_lines():
    body = (
        "# P\n\n## Key points\n\n"
        "- Pages under `wiki/` are owned by the AI agent, using double-bracket\n"
        "  wikilinks to connect related pages.\n"
        "- Second point.\n\n"
        "## Related\n\nx\n"
    )
    masked = mask_non_prose(body)
    points = extract_key_points(body, masked)
    assert points == [
        "Pages under `wiki/` are owned by the AI agent, using double-bracket "
        "wikilinks to connect related pages.",
        "Second point.",
    ]


def test_content_hash_changes_with_content():
    a = parse_page("body a\n", "p.md")
    b = parse_page("body b\n", "p.md")
    assert a.content_hash != b.content_hash


def test_extract_related_links_from_frontmatter_list():
    fm = {"related": ["wiki/concepts/foo", "wiki/decisions/bar"]}
    links = extract_related_links(fm)
    assert [link.target_raw for link in links] == [
        "wiki/concepts/foo",
        "wiki/decisions/bar",
    ]
    assert all(link.kind == "related" for link in links)


def test_extract_related_links_absent_is_empty():
    assert extract_related_links({}) == []


def test_parse_page_includes_related_links_alongside_wikilinks():
    text = (
        "---\n"
        "title: A\n"
        "related:\n"
        "  - wiki/concepts/foo\n"
        "---\n"
        "See [[B]].\n"
    )
    page = parse_page(text, "wiki/decisions/a.md")
    kinds = {link.kind for link in page.links}
    assert kinds == {"wikilink", "related"}


def test_parse_page_accepts_last_updated_synonym():
    text = "---\ntitle: A\nlast_updated: 2026-07-01\n---\nbody\n"
    page = parse_page(text, "p.md")
    assert page.updated == "2026-07-01"


def test_markdown_link_url_decodes_spaces_and_unicode():
    text = "[Project Profile](wiki/overview/Project%20Profile.md)\n"
    masked = mask_non_prose(text)
    md_links, _ = extract_markdown_links(masked)
    assert md_links[0].target_raw == "wiki/overview/Project Profile.md"
