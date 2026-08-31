"""What still has to work when the environment around llmw is damaged.

Three surfaces, one rule: **a read surface degrades, it does not refuse,
and a guard degrades to protecting rather than to standing aside.**

Each case here was found by probing rather than by reasoning, and each
had already survived four rounds of review of the code that contains it.

- A `config.toml` with a typo raised `ConfigError` inside the PreToolUse
  hook. `hook_entry.run_event` swallows everything so a hook can never
  break a tool call — which meant the raw/ immutability guard and the
  wiki write guard silently switched **off**, with no message anywhere.
  Verified against the shipped binary before the fix.
- A damaged index — `pages_fts` or `links` dropped by an interrupted
  write or a half-synced folder — crashed `llmw search` and `llmw read`
  with a raw `OperationalError`. `open_ro` only probed `sqlite_master`,
  so it called a structurally incomplete database readable. Same class as
  the pre-0.1.31 column crash.
- A `tool_input` that is a string rather than a mapping raised through
  the evaluate functions. Harmless through the hook entry, which catches
  it, but the entry catching everything is exactly why the two above went
  unnoticed for so long.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.hook import evaluate_pretooluse
from llmw.indexer import rebuild
from llmw.paths import ProjectPaths
from llmw.read import read_page
from llmw.search import IndexNotBuiltError, search

PAGE = (
    "---\ntitle: T\ntype: note\nstatus: active\ncreated: 2026-06-01\n"
    "updated: 2026-06-01\nsummary: s.\n---\n\n# T\n\nRetry budget body.\n"
)

BROKEN_CONFIGS = {
    "not toml at all": "this is not toml {{{\n",
    "unclosed table": "[hooks\n",
    "value is not a value": "[hooks]\nwiki_guard =\n",
}


def _project(tmp_path: Path) -> ProjectPaths:
    init_project(tmp_path)
    paths = ProjectPaths.for_project_root(tmp_path)
    page = tmp_path / "wiki" / "decisions" / "t.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(PAGE, encoding="utf-8")
    (tmp_path / "raw").mkdir(exist_ok=True)
    (tmp_path / "raw" / "note.md").write_text("immutable\n", encoding="utf-8")
    rebuild(paths)
    return paths


def _write_payload(paths: ProjectPaths, target: Path) -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": "x"},
        "session_id": "degraded",
        "cwd": str(paths.project_root),
    }


@pytest.mark.parametrize("name", sorted(BROKEN_CONFIGS))
def test_a_broken_config_does_not_switch_the_guards_off(
    name: str, tmp_path: Path
) -> None:
    # The guard exists to stop an accidental write to an immutable file.
    # Losing it because a config file has a typo trades a real protection
    # for a parse error nobody sees.
    paths = _project(tmp_path)
    paths.config_path.write_text(BROKEN_CONFIGS[name], encoding="utf-8")

    result = evaluate_pretooluse(_write_payload(paths, tmp_path / "raw" / "note.md"))

    assert result is not None, f"{name}: guard went silent"
    decision = result["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
    assert "raw/" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_a_broken_config_still_guards_wiki_writes(tmp_path: Path) -> None:
    paths = _project(tmp_path)
    paths.config_path.write_text("this is not toml {{{\n", encoding="utf-8")

    result = evaluate_pretooluse(
        _write_payload(paths, tmp_path / "wiki" / "decisions" / "t.md")
    )

    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_a_broken_config_is_still_reported_by_health(tmp_path: Path) -> None:
    # Falling back to defaults must not make the problem invisible: the
    # hook stays quiet by design, so something else has to say it.
    from llmw.health import check_health

    paths = _project(tmp_path)
    paths.config_path.write_text("this is not toml {{{\n", encoding="utf-8")

    report = check_health(paths)

    assert not report.is_healthy()
    assert report.checks.get("config_readable") is False


@pytest.mark.parametrize("dropped", ["pages_fts", "links"])
def test_a_damaged_index_says_to_rebuild_instead_of_crashing(
    dropped: str, tmp_path: Path
) -> None:
    # An interrupted write or a half-synced folder leaves tables missing.
    # `open_ro` probed only `sqlite_master`, so it called that readable
    # and the missing table surfaced as a raw OperationalError on the
    # command the skill runs first.
    paths = _project(tmp_path)
    conn = sqlite3.connect(paths.index_db)
    try:
        conn.execute(f"DROP TABLE {dropped}")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(IndexNotBuiltError):
        search(paths, "retry", limit=3)

    # `read` works from the file on disk, so it must still answer — it
    # simply knows nothing about links or backlinks.
    result = read_page(paths, "wiki/decisions/t.md")
    assert result.title == "T"
    assert result.indexed is False


def test_a_garbage_index_file_says_to_rebuild(tmp_path: Path) -> None:
    paths = _project(tmp_path)
    paths.index_db.write_bytes(b"not a database at all")

    with pytest.raises(IndexNotBuiltError):
        search(paths, "retry", limit=3)
    assert read_page(paths, "wiki/decisions/t.md").title == "T"


MALFORMED_PAYLOADS = {
    "tool_input is a string": {"tool_name": "Edit", "tool_input": "oops"},
    "tool_input is a list": {"tool_name": "Edit", "tool_input": []},
    "file_path is a mapping": {"tool_name": "Edit", "tool_input": {"file_path": {}}},
    "command is a list": {"tool_name": "Bash", "tool_input": {"command": ["ls"]}},
    "nothing at all": {},
}


@pytest.mark.parametrize("name", sorted(MALFORMED_PAYLOADS))
def test_a_malformed_payload_is_answered_not_raised(name: str, tmp_path: Path) -> None:
    paths = _project(tmp_path)
    payload = {**MALFORMED_PAYLOADS[name], "cwd": str(tmp_path), "session_id": "s"}

    evaluate_pretooluse(payload)  # must not raise


@pytest.mark.parametrize(
    "blob", ["not json", "[1,2,3]", '"hello"', "", "null", "{" * 1000]
)
def test_the_hook_entry_exits_clean_on_any_stdin(blob: str, tmp_path: Path) -> None:
    # The outermost guarantee: whatever a host sends, the hook exits 0 and
    # says nothing rather than failing the tool call it was asked about.
    _project(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "llmw.cli", "hook", "pretooluse"],
        input=blob,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    if result.stdout.strip():
        json.loads(result.stdout)


DANGEROUS_SESSION_IDS = [
    "../../evil",
    "/etc/passwd",
    "C:\\Windows\\evil",
    "a" * 500,
    "",
    "..",
    "a\x00b",
]


@pytest.mark.parametrize("session_id", DANGEROUS_SESSION_IDS)
def test_a_session_id_never_becomes_a_path(session_id: str, tmp_path: Path) -> None:
    # The value lands in a filesystem path, so the sanitizer is the only
    # thing between a host's session id and an arbitrary write.
    from llmw.hook_state import read_session_state, write_session_state

    paths = _project(tmp_path)
    before = {p for p in tmp_path.rglob("*") if p.is_file()}

    write_session_state(paths, session_id, dirty=True)

    assert read_session_state(paths, session_id) == {}
    assert {p for p in tmp_path.rglob("*") if p.is_file()} == before


def test_adopt_says_the_index_still_has_to_be_built(tmp_path: Path) -> None:
    """`--adopt` points llmw at a wiki that already has content.

    `init` builds no index, which is right for an empty project and
    leaves an adopted one in a state where the very next command —
    `llmw search`, which the skill runs first — fails with "Index not
    built yet". The user just told the tool there is content; it should
    say what to do with it.
    """
    (tmp_path / "wiki" / "decisions").mkdir(parents=True)
    (tmp_path / "wiki" / "decisions" / "a.md").write_text(PAGE, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "llmw.cli", "init", "--adopt"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert "llmw rebuild" in result.stdout, result.stdout


def test_a_plain_init_does_not_nag_about_rebuilding(tmp_path: Path) -> None:
    # An empty project has nothing to index, so the hint would be noise.
    result = subprocess.run(
        [sys.executable, "-m", "llmw.cli", "init"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert "llmw rebuild" not in result.stdout, result.stdout
