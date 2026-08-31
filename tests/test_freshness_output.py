"""`search` and `read` must show how old a page's claims are.

A wiki page that records *mechanism* — the real A→B→C chain with file and
function names — is the most useful thing in the wiki and the first thing
to rot when the code moves. The failure that costs something is not the
rotting; it is reading a rotted page as current and judging from it.

Neither surface used to carry a freshness signal at all: `search` printed
path/score/summary/links and dropped `SearchResult.title` and `.status`
on the floor, and `read --brief` printed `status` but no date. So a page
titled "... (v0.1.18)", last updated seven weeks ago, came back looking
exactly like one written this morning.

These tests pin the three signals that cost nothing to produce, in
descending order of how hard they are to skim past:

1. the title, which by convention carries an era stamp — "(v0.1.18)";
2. a non-`active` status, on the path line itself, so it cannot be read
   without reading the path the agent is about to act on;
3. `updated`, with a relative age, and — when the index has *observed*
   the body change since the page's own claim — both numbers rather than
   whichever one we happened to prefer. That gap is itself the evidence:
   the body changed without anyone restating when the claims were last
   true.

The third keys on the body, not the file. A file-based version shipped
first and put a permanent divergence note on 21 of this project's own 31
pages after a single frontmatter-only sweep — declaring `code:`, marking
a page superseded, and fixing a tag all rewrite the file while restating
nothing, and the write-side rule says correctly not to bump `updated` for
them.
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _days_ago(days: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def _seed(root: Path, name: str, *, title: str, status: str, updated: str) -> Path:
    page = root / "wiki" / "decisions" / f"{name}.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "---\n"
        f"title: {title}\n"
        "type: decision\n"
        f"status: {status}\n"
        f"created: {updated}\n"
        f"updated: {updated}\n"
        "summary: The retry budget lives in the uploader, not the client.\n"
        "---\n"
        "# Retry budget\n\nThe uploader owns the retry budget.\n",
        encoding="utf-8",
    )
    return page


def _project(tmp_path: Path, **kwargs) -> subprocess.CompletedProcess:
    run(tmp_path, "init")
    _seed(tmp_path, "retry-budget", **kwargs)
    return run(tmp_path, "rebuild")


def test_search_prints_the_page_title(tmp_path: Path) -> None:
    # The era stamp pages carry by convention is in the title and nowhere
    # else. Dropping it is the cheapest staleness signal to lose.
    _project(
        tmp_path,
        title="Retry budget moves into the uploader (v0.1.18)",
        status="active",
        updated=_days_ago(49),
    )

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert "Retry budget moves into the uploader (v0.1.18)" in result.stdout


def test_search_prints_updated_with_a_relative_age(tmp_path: Path) -> None:
    # An ISO date makes the reader know today's date and subtract. The
    # relative age is what actually registers while skimming.
    updated = _days_ago(49)
    _project(tmp_path, title="Retry budget", status="active", updated=updated)

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert updated in result.stdout
    assert "49d ago" in result.stdout


def test_a_page_we_have_only_ever_seen_once_reports_no_divergence(
    tmp_path: Path,
) -> None:
    # Divergence is a claim about history: the body changed *after* the
    # page said when it was last restated. On a page indexed for the first
    # time there is no history, so the honest answer is to say nothing.
    # Keying on the file's mtime instead would fire on every page of a
    # fresh clone, and on every page any metadata edit ever touched.
    _project(
        tmp_path, title="Retry budget", status="active", updated=_days_ago(200)
    )

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert _days_ago(200) in result.stdout
    assert "body changed" not in result.stdout


def test_a_body_edit_that_leaves_the_claim_behind_shows_the_gap(
    tmp_path: Path,
) -> None:
    _project(
        tmp_path, title="Retry budget", status="active", updated=_days_ago(200)
    )

    run(
        tmp_path, "edit", "wiki/decisions/retry-budget.md",
        "--old", "The uploader owns the retry budget.",
        "--new", "The client owns the retry budget again.",
        "--reason", "reverse it",
    )
    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert _days_ago(200) in result.stdout
    assert "body changed" in result.stdout
    assert datetime.date.today().isoformat() in result.stdout


def test_a_frontmatter_only_edit_reports_no_divergence(tmp_path: Path) -> None:
    # This is the case that broke the mtime version. Declaring `code:`,
    # marking a page superseded, fixing a tag — all rewrite the file
    # without restating a single claim, and the write-side rule says
    # correctly not to bump `updated` for them. Keying on bytes put a
    # permanent divergence note on 21 of this project's own 31 pages after
    # one sweep. The read side now uses the same basis the writer's own
    # unbumped-`updated` notice uses: the body.
    _project(
        tmp_path, title="Retry budget", status="active", updated=_days_ago(200)
    )

    run(
        tmp_path, "edit", "wiki/decisions/retry-budget.md",
        "--old", "type: decision", "--new", "type: decision\ntags:\n  - retries",
        "--reason", "tag it",
    )
    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert "body changed" not in result.stdout


def test_read_reports_divergence_on_the_same_basis(tmp_path: Path) -> None:
    _project(
        tmp_path, title="Retry budget", status="active", updated=_days_ago(200)
    )
    run(
        tmp_path, "edit", "wiki/decisions/retry-budget.md",
        "--old", "The uploader owns the retry budget.",
        "--new", "The client owns the retry budget again.",
        "--reason", "reverse it",
    )

    result = run(tmp_path, "read", "wiki/decisions/retry-budget.md")

    assert result.returncode == 0, result.stderr
    assert "body changed" in result.stdout


def test_search_flags_a_non_active_status_on_the_path_line(tmp_path: Path) -> None:
    # On the path line specifically: the agent cannot read the path it is
    # about to act on without reading the flag. A separate line gets
    # skimmed past.
    _project(
        tmp_path,
        title="Retry budget",
        status="superseded",
        updated=_days_ago(49),
    )

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    path_line = next(
        line for line in result.stdout.splitlines() if "retry-budget.md" in line
    )
    assert "superseded" in path_line


def test_search_does_not_flag_an_active_status(tmp_path: Path) -> None:
    # `active` is the overwhelming majority; printing it would be noise
    # that trains the reader to ignore the field.
    _project(tmp_path, title="Retry budget", status="active", updated=_days_ago(49))

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    path_line = next(
        line for line in result.stdout.splitlines() if "retry-budget.md" in line
    )
    assert "active" not in path_line


def test_search_json_carries_updated(tmp_path: Path) -> None:
    updated = _days_ago(49)
    _project(tmp_path, title="Retry budget", status="active", updated=updated)

    result = run(tmp_path, "search", "retry budget", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["results"][0]["updated"] == updated


def test_read_brief_prints_updated_with_a_relative_age(tmp_path: Path) -> None:
    updated = _days_ago(49)
    _project(tmp_path, title="Retry budget", status="active", updated=updated)

    result = run(tmp_path, "read", "wiki/decisions/retry-budget.md")

    assert result.returncode == 0, result.stderr
    assert updated in result.stdout
    assert "49d ago" in result.stdout


def test_read_full_output_stays_byte_exact(tmp_path: Path) -> None:
    # `read --full` is what an agent snapshots before computing a series
    # of `llmw edit --old/--new` calls, so its stdout must remain the file
    # and nothing else. Any freshness framing on this surface belongs on
    # stderr.
    _project(tmp_path, title="Retry budget", status="active", updated=_days_ago(200))
    page = tmp_path / "wiki" / "decisions" / "retry-budget.md"

    result = run(tmp_path, "read", "wiki/decisions/retry-budget.md", "--full")

    assert result.returncode == 0, result.stderr
    # `print` contributes the one trailing newline; nothing else may be
    # added. This page diverges by 200 days, so the search/brief surfaces
    # would both annotate it — this one must not.
    assert result.stdout == page.read_text(encoding="utf-8") + "\n"
    assert "file modified" not in result.stdout
    assert "d ago" not in result.stdout


def test_mcp_search_and_read_carry_the_freshness_fields(tmp_path: Path) -> None:
    # The Codex skill tells an agent working through MCP to check
    # `updated` before trusting a page's file/function detail, and Claude's
    # PreToolUse matcher lists `mcp__llm-wiki__llmw_search`, so this is a
    # live read surface here too. The guidance is only true while
    # `llmw_search`/`llmw_read` return `as_dict()` verbatim
    # (`mcp_server.py:53`, `:59`) — the day either hand-builds a payload,
    # the instruction points at a field the host never sees and nothing
    # else would notice.
    from llmw import mcp_server

    updated = _days_ago(49)
    _project(tmp_path, title="Retry budget", status="active", updated=updated)

    found = mcp_server.llmw_search("retry budget", root=str(tmp_path))
    assert found["results"][0]["updated"] == updated
    # None on a page seen once: there is no observed history to report.
    assert "body_changed_at" in found["results"][0]

    page_payload = mcp_server.llmw_read(
        "wiki/decisions/retry-budget.md", root=str(tmp_path)
    )
    assert page_payload["updated"] == updated
    assert "body_changed_at" in page_payload
