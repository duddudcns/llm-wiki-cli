"""The writer tells the agent what it just left incomplete.

Two gaps, both found the same way: by writing a page during a real
session and only noticing later.

A page written with no frontmatter at all sat in this repo's own wiki
until `llmw lint` was run by hand. `lint` had always caught it —
`missing_frontmatter` names the exact keys — but nothing invokes lint, so
the check existed and never fired. The same is true of `updated`: it is
the field every freshness signal keys on, and `edit`/`patch` write a new
body straight past it.

Neither is a reason to reject the write. Half these calls are legitimate
non-page content, and refusing an edit to an already-nonconforming page
would deadlock it — `llmw edit` would refuse while the wiki guard denies
native edits, leaving only a fully reconstructed `write --force` that
nothing tells the agent about. A notice is enough: the agent is still in
context and can fire the follow-up itself.

Notices go to stderr so they never enter a stream something parses.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

COMPLETE = """---
title: Retry budget
type: decision
status: active
created: 2026-06-01
updated: 2026-06-01
summary: Who counts retries.
---

# Retry budget

The uploader owns the retry budget.
"""

PAGE = "wiki/decisions/retry-budget.md"


def run(cwd: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "COLUMNS": "200"},
    )


def _seeded(tmp_path: Path, content: str = COMPLETE) -> Path:
    run(tmp_path, "init")
    run(tmp_path, "write", PAGE, "--reason", "seed", "--stdin", stdin=content)
    return tmp_path / PAGE


def test_write_names_the_frontmatter_keys_it_is_missing(tmp_path: Path) -> None:
    run(tmp_path, "init")

    result = run(
        tmp_path, "write", PAGE, "--reason", "r", "--stdin",
        stdin="# Retry budget\n\nThe uploader owns it.\n",
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / PAGE).exists(), "the page is still written; this is a notice"
    for key in ("type", "status", "created", "updated"):
        assert key in result.stderr
    assert result.stderr.count("\n") <= 2, "one line, not a wall of text"


def test_a_complete_page_gets_no_notice(tmp_path: Path) -> None:
    run(tmp_path, "init")

    result = run(tmp_path, "write", PAGE, "--reason", "r", "--stdin", stdin=COMPLETE)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_edit_flags_a_body_change_that_left_updated_behind(tmp_path: Path) -> None:
    # The whole freshness display keys on `updated`, and it is maintained
    # by the same convention that produced the staleness problem.
    _seeded(tmp_path)

    result = run(
        tmp_path, "edit", PAGE,
        "--old", "The uploader owns the retry budget.\n",
        "--new", "The client owns the retry budget again.\n",
        "--reason", "reverse the decision",
    )

    assert result.returncode == 0, result.stderr
    assert "updated" in result.stderr
    assert "2026-06-01" in result.stderr


def test_restating_the_claim_in_the_same_write_is_silent(tmp_path: Path) -> None:
    # `edit` replaces one contiguous string, so a body change and an
    # `updated` bump cannot ride in the same call — the notice firing on
    # each half separately is correct, and is what prompts the second one.
    # `patch` can do both at once, and then there is nothing to say.
    _seeded(tmp_path)
    diff = (
        f"--- a/{PAGE}\n+++ b/{PAGE}\n"
        "@@ -5,3 +5,3 @@\n"
        " created: 2026-06-01\n"
        "-updated: 2026-06-01\n"
        "+updated: 2026-08-31\n"
        " summary: Who counts retries.\n"
        "@@ -10,3 +10,3 @@\n"
        " # Retry budget\n \n"
        "-The uploader owns the retry budget.\n"
        "+The client owns the retry budget again.\n"
    )

    result = run(tmp_path, "patch", PAGE, "--reason", "reverse", "--stdin", stdin=diff)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""


def test_an_edit_that_only_touches_frontmatter_is_silent(tmp_path: Path) -> None:
    # Nothing was claimed differently, so there is nothing to restate.
    _seeded(tmp_path)

    result = run(
        tmp_path, "edit", PAGE, "--old", "type: decision", "--new", "type: note",
        "--reason", "reclassify",
    )

    assert result.returncode == 0, result.stderr
    assert "not bumped" not in result.stderr


def test_patch_flags_it_too(tmp_path: Path) -> None:
    _seeded(tmp_path)
    diff = (
        # Frontmatter occupies lines 1-8; the heading is on line 10.
        f"--- a/{PAGE}\n+++ b/{PAGE}\n@@ -10,3 +10,3 @@\n"
        " # Retry budget\n \n"
        "-The uploader owns the retry budget.\n"
        "+The client owns the retry budget again.\n"
    )

    result = run(tmp_path, "patch", PAGE, "--reason", "reverse", "--stdin", stdin=diff)

    assert result.returncode == 0, result.stderr
    assert "updated" in result.stderr


def test_notices_never_reach_stdout(tmp_path: Path) -> None:
    # stdout is the machine-readable half of every command here.
    run(tmp_path, "init")

    result = run(
        tmp_path, "write", PAGE, "--reason", "r", "--stdin", stdin="# bare\n"
    )

    assert result.stdout.strip() == f"wrote {PAGE}"


def test_mcp_returns_the_notices_instead_of_printing_them(tmp_path: Path) -> None:
    # An MCP host has no stderr to read, so the same information has to
    # travel in the response or Codex never sees it.
    from llmw import mcp_server

    run(tmp_path, "init")

    result = mcp_server.llmw_write(
        PAGE, "# bare\n", reason="r", root=str(tmp_path)
    )

    assert result["written"] is True
    assert any("updated" in notice for notice in result["notices"])
