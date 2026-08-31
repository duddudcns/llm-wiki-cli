"""Superseding a decision must write both sides, or neither.

A new decision that overturns an old one already links back to it — the
agent does that unprompted. What never happens is the reverse pointer:
nothing marks the old page, so `llmw search` keeps returning it as
`status: active` and a later session reads a decision that was reversed
weeks ago. Three instances of exactly this are recorded in this repo's own
`log.md` as free-text body edits with the status left alone.

That is the failure mode a convention cannot fix, because forgetting the
second write in a different file is how the problem arose in the first
place. `llmw write --supersedes` makes it one operation instead of two,
so it cannot be half-done.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from llmw.frontmatter import split_frontmatter

OLD = "wiki/decisions/retry-in-the-client.md"
NEW = "wiki/decisions/retry-in-the-uploader.md"

NEW_CONTENT = """---
title: Retry budget moves into the uploader
type: decision
status: active
created: 2026-08-31
updated: 2026-08-31
summary: The uploader owns the retry budget now.
---

# Retry budget moves into the uploader

The client no longer counts retries.
"""


def run(cwd: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    # A wide terminal so Rich does not soft-wrap a long path line: these
    # tests are about what is on one *logical* line, not about how an
    # 80-column terminal folds it.
    env = {**os.environ, "COLUMNS": "200"}
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _project(tmp_path: Path, *, old_frontmatter: bool = True) -> Path:
    run(tmp_path, "init")
    old = tmp_path / OLD
    old.parent.mkdir(parents=True, exist_ok=True)
    head = (
        "---\ntitle: Retry budget lives in the client\ntype: decision\n"
        "status: active\ncreated: 2026-06-01\nupdated: 2026-06-01\n"
        "summary: The client counts retries.\n---\n"
        if old_frontmatter
        else ""
    )
    old.write_text(
        head + "# Retry budget lives in the client\n\nThe client counts retries.\n",
        encoding="utf-8",
    )
    run(tmp_path, "rebuild")
    return old


def _frontmatter(path: Path) -> dict:
    return split_frontmatter(path.read_text(encoding="utf-8"))[0]


def test_supersede_writes_both_sides(tmp_path: Path) -> None:
    old = _project(tmp_path)

    result = run(
        tmp_path,
        "write",
        NEW,
        "--reason",
        "the uploader owns retries now",
        "--supersedes",
        OLD,
        "--stdin",
        stdin=NEW_CONTENT,
    )

    assert result.returncode == 0, result.stderr
    assert _frontmatter(tmp_path / NEW)["supersedes"] == OLD
    old_fm = _frontmatter(old)
    assert old_fm["status"] == "superseded"
    assert old_fm["superseded_by"] == NEW


def test_supersede_preserves_the_rest_of_the_old_page(tmp_path: Path) -> None:
    # The flip is a metadata operation. It must not disturb the body, which
    # still holds the durable "why" that outlives the decision itself.
    old = _project(tmp_path)

    run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )

    # Asserted on the text, not the parsed mapping: the guarantee is that
    # the author's key order and formatting survive, and `set_fields`
    # re-dumps the block whenever a key has to be replaced (`status` here).
    # An unquoted `created: 2026-06-01` parses to a `datetime.date` both
    # before and after, so comparing parsed values would prove nothing.
    text = old.read_text(encoding="utf-8")
    assert "The client counts retries." in text
    assert "title: Retry budget lives in the client\n" in text
    assert "created: 2026-06-01\n" in text
    assert "updated: 2026-06-01\n" in text
    assert "summary: The client counts retries.\n" in text


def test_supersede_backs_up_and_logs_both_pages(tmp_path: Path) -> None:
    # The old-page flip is a mutation like any other and goes through the
    # same safety machinery, or it is a write that cannot be undone or
    # audited.
    _project(tmp_path)

    run(
        tmp_path, "write", NEW, "--reason", "the uploader owns retries", "--supersedes",
        OLD, "--stdin", stdin=NEW_CONTENT,
    )

    assert list((tmp_path / ".llmw" / "backups").rglob("retry-in-the-client.md"))
    log = (tmp_path / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "retry-in-the-uploader.md" in log
    assert "retry-in-the-client.md" in log


def test_supersede_stamps_frontmatter_onto_a_page_that_has_none(
    tmp_path: Path,
) -> None:
    # Same situation `llmw archive` already handles: a lifecycle operation
    # whose whole purpose is to set metadata cannot refuse a page that has
    # no metadata block yet.
    old = _project(tmp_path, old_frontmatter=False)

    result = run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )

    assert result.returncode == 0, result.stderr
    fm = _frontmatter(old)
    assert fm["status"] == "superseded"
    assert fm["superseded_by"] == NEW
    assert "The client counts retries." in old.read_text(encoding="utf-8")


def test_supersede_refuses_an_unknown_target_and_writes_nothing(
    tmp_path: Path,
) -> None:
    # Half-done is the failure this command exists to prevent, so a bad
    # target must not leave the new page behind claiming to supersede
    # something that was never marked.
    _project(tmp_path)

    result = run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes",
        "wiki/decisions/never-existed.md", "--stdin", stdin=NEW_CONTENT,
    )

    assert result.returncode != 0
    assert not (tmp_path / NEW).exists()


def test_supersede_refuses_to_point_a_page_at_itself(tmp_path: Path) -> None:
    _project(tmp_path)

    result = run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", NEW, "--stdin",
        stdin=NEW_CONTENT,
    )

    assert result.returncode != 0
    assert not (tmp_path / NEW).exists()


def test_the_parser_exposes_supersession_as_links(tmp_path: Path) -> None:
    # `extract_related_links` read only `related:`, so any other
    # frontmatter key was dropped at parse — invisible to the index, to
    # `llmw links`/`backlinks`, and to the search flag below.
    from llmw.parser import parse_page

    page = parse_page(
        "---\ntitle: New\nsupersedes: " + OLD + "\n---\nbody\n", NEW
    )

    kinds = {link.kind: link.target_raw for link in page.links}
    assert kinds["supersedes"] == OLD


def test_search_names_the_page_that_replaced_this_one(tmp_path: Path) -> None:
    _project(tmp_path)
    run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "search", "retry budget client")

    assert result.returncode == 0, result.stderr
    path_line = next(
        line
        for line in result.stdout.splitlines()
        if "retry-in-the-client.md" in line
    )
    assert "superseded" in path_line
    assert "retry-in-the-uploader.md" in path_line


def test_the_flip_does_not_leave_a_permanent_divergence_notice(
    tmp_path: Path,
) -> None:
    # Marking a page superseded rewrites its frontmatter, so its mtime
    # jumps past its `updated` — but the body's claims were not restated,
    # they were retired. Reporting "file modified" here would fire on
    # every superseded page forever and dilute the notice everywhere else,
    # and the flag already says louder than a date that this page is not
    # the current answer.
    _project(tmp_path)
    run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "search", "retry budget client")

    assert result.returncode == 0, result.stderr
    block = result.stdout.split("retry-in-the-client.md", 1)[1].split("\n2. ")[0]
    assert "2026-06-01" in block
    assert "file modified" not in block


def test_backlinks_see_the_supersession(tmp_path: Path) -> None:
    _project(tmp_path)
    run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "backlinks", OLD)

    assert result.returncode == 0, result.stderr
    assert "retry-in-the-uploader.md" in result.stdout


def test_mcp_write_can_supersede_too(tmp_path: Path) -> None:
    # Codex only ever reaches the writer through MCP, and its rules now
    # tell it to supersede rather than leave an overturned page active.
    # A flag the CLI has and the MCP tool does not is guidance that
    # silently cannot be followed on one of the two platforms.
    from llmw import mcp_server

    old = _project(tmp_path)

    result = mcp_server.llmw_write(
        NEW,
        NEW_CONTENT,
        reason="the uploader owns retries now",
        root=str(tmp_path),
        supersedes=OLD,
    )

    assert result["superseded"] == OLD
    old_fm = _frontmatter(old)
    assert old_fm["status"] == "superseded"
    assert old_fm["superseded_by"] == NEW


def test_a_superseded_page_keeps_valid_yaml(tmp_path: Path) -> None:
    # The stamped block is re-parsed by every later read; a dump that
    # produced something PyYAML rejects would brick the page.
    old = _project(tmp_path)
    run(
        tmp_path, "write", NEW, "--reason", "r", "--supersedes", OLD, "--stdin",
        stdin=NEW_CONTENT,
    )

    text = old.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    body_start = text.index("\n---\n", 3) + len("\n---\n")
    assert yaml.safe_load(text[4 : body_start - len("\n---\n") + 1]) is not None
