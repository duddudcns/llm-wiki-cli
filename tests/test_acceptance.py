"""Acceptance tests mirroring spec section 14 — run against the built
console-script `llmw`, exercised as a real subprocess (as an agent would).
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


def test_14_1_init(tmp_path: Path):
    result = run(tmp_path, "init")
    assert result.returncode == 0, result.stderr

    assert (tmp_path / "raw").is_dir()
    assert (tmp_path / "wiki").is_dir()
    assert (tmp_path / ".llmw").is_dir()
    assert (tmp_path / "wiki" / "index.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "llm-wiki" / "SKILL.md").is_file()


def test_14_2_wikilink_parsing(tmp_path: Path):
    run(tmp_path, "init")
    fixture = (
        "# A\n\n"
        "Links: [[B]], [[C|see C]], [[D#Part|D part]], ![[E]]\n\n"
        "```text\n[[Ignored]]\n```\n"
    )
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(fixture, encoding="utf-8")

    result = run(tmp_path, "rebuild")
    assert result.returncode == 0, result.stderr

    result = run(tmp_path, "links", "A", "--json")
    assert result.returncode == 0, result.stderr
    targets = [item["target"] for item in json.loads(result.stdout)]
    assert "B" in targets
    assert "C" in targets
    assert "D" in targets
    assert "E" in targets
    assert "Ignored" not in targets


def test_14_3_backlinks(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(
        "---\ntitle: A\n---\nSee [[B]].\n", encoding="utf-8"
    )
    (tmp_path / "wiki" / "concepts" / "b.md").write_text(
        "---\ntitle: B\n---\nbody\n", encoding="utf-8"
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "backlinks", "B", "--json")
    assert result.returncode == 0, result.stderr
    items = json.loads(result.stdout)
    assert any(item["source"] == "wiki/concepts/a.md" for item in items)


def test_14_4_broken_link(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(
        "---\ntitle: A\n---\nSee [[Missing]].\n", encoding="utf-8"
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "lint", "--json")
    assert result.returncode == 1  # lint exits non-zero when issues are found
    report = json.loads(result.stdout)
    assert {"source": "wiki/concepts/a.md", "target": "Missing"} in report["broken_links"]


def test_14_5_search(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(
        "---\ntitle: A\n---\nThis page discusses context window overhead.\n",
        encoding="utf-8",
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "search", "context overhead", "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "strict"
    assert any(r["path"] == "wiki/concepts/a.md" for r in report["results"])


def test_14_6_archive(tmp_path: Path):
    run(tmp_path, "init")
    (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "wiki" / "concepts" / "a.md").write_text(
        "---\ntitle: A\n---\nbody\n", encoding="utf-8"
    )
    run(tmp_path, "rebuild")

    result = run(tmp_path, "archive", "wiki/concepts/a.md", "--reason", "duplicate")
    assert result.returncode == 0, result.stderr

    archived_files = list((tmp_path / "wiki" / "archived").glob("**/*.md"))
    assert len(archived_files) >= 1
    log_text = (tmp_path / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "archive" in log_text
    assert "duplicate" in log_text


def test_14_7_no_raw_modification(tmp_path: Path):
    run(tmp_path, "init")
    result = run(
        tmp_path, "write", "raw/test.md", "--reason", "bad", "--stdin", input="bad content\n"
    )
    assert result.returncode != 0
    assert "raw/" in (result.stderr + result.stdout)
    assert not (tmp_path / "raw" / "test.md").is_file()
