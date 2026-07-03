"""Regression tests: wiki content must never be interpreted as rich markup,
and JSON output must never be line-wrapped, since both would corrupt or
crash the machine-readable interface an agent depends on.
"""

import json
import subprocess
import sys
from pathlib import Path


def run(cwd: Path, *args: str, input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", *args],
        cwd=cwd,
        input=input,
        capture_output=True,
        text=True,
    )


def test_bracket_shaped_content_does_not_crash_or_corrupt_json(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    long_value = "x" * 150
    (tmp_path / "wiki" / "concepts" / "errors.md").write_text(
        "---\n"
        "title: Error Codes\n"
        f"summary: See [/nonexistent] and [bold]this[/bold] and {long_value}\n"
        "---\n"
        "body with [LEA-3004] error\n",
        encoding="utf-8",
    )
    result = run(tmp_path, "rebuild")
    assert result.returncode == 0, result.stderr

    result = run(tmp_path, "read", "Error Codes", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["summary"] == f"See [/nonexistent] and [bold]this[/bold] and {long_value}"


def test_bracket_shaped_content_does_not_crash_human_readable_read(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "errors.md").write_text(
        '---\ntitle: Error Codes\nsummary: "[/mismatched] tag"\n---\nbody\n',
        encoding="utf-8",
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "read", "Error Codes")
    assert result.returncode == 0, result.stderr
    assert "[/mismatched] tag" in result.stdout


def test_long_json_value_is_not_line_wrapped(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    long_value = "y" * 200
    (tmp_path / "wiki" / "concepts" / "long.md").write_text(
        f"---\ntitle: Long\nsummary: {long_value}\n---\nbody\n", encoding="utf-8"
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "search", "long", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)  # would raise if the value got split by a hard newline
    assert any(r["summary"] == long_value for r in payload["results"])


def test_lint_json_output_is_valid_even_with_bracket_content(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(
        "---\ntitle: A\n---\nSee [[Missing/with[brackets]]].\n", encoding="utf-8"
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "lint", "--json")
    assert result.returncode in (0, 1)
    json.loads(result.stdout)  # must not raise
