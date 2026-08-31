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
3. `updated`, with a relative age, and — when the file on disk is newer
   than the page's own claim — both numbers rather than whichever one we
   happened to prefer. That gap is itself the evidence: it means the body
   changed without anyone restating when the claims were last true.
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


def test_search_shows_both_dates_when_the_file_is_newer_than_its_claim(
    tmp_path: Path,
) -> None:
    # The page says its claims were last restated 200 days ago, but the
    # file was written today: somebody edited the body and left `updated`
    # alone. Show the gap instead of picking a winner — substituting the
    # file mtime would quietly relabel "last touched" as "last verified".
    _project(
        tmp_path, title="Retry budget", status="active", updated=_days_ago(200)
    )

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert _days_ago(200) in result.stdout
    assert "file modified" in result.stdout
    assert datetime.date.today().isoformat() in result.stdout


def test_search_does_not_report_divergence_for_a_page_updated_today(
    tmp_path: Path,
) -> None:
    # Every page is written to disk "now" during a test, so the divergence
    # notice has to key on a real gap or it would fire on every result and
    # become invisible.
    _project(tmp_path, title="Retry budget", status="active", updated=_days_ago(0))

    result = run(tmp_path, "search", "retry budget")

    assert result.returncode == 0, result.stderr
    assert "file modified" not in result.stdout


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
