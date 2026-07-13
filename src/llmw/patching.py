"""Minimal unified-diff applier for `llmw patch`.

Deliberately dependency-free and strict: every context/removed line must
match the source exactly at its recorded position, or the whole patch is
rejected before anything is written.
"""

from __future__ import annotations

import re

_HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_len>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_len>\d+))? @@"
)
_NO_NEWLINE_MARKER = r"\ No newline at end of file"


class PatchApplyError(RuntimeError):
    pass


def _parse_hunks(diff_text: str) -> list[dict]:
    lines = diff_text.splitlines()
    hunks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue
        match = _HUNK_HEADER_RE.match(line)
        if not match:
            i += 1
            continue
        old_start = int(match.group("old_start"))
        old_len = int(match.group("old_len")) if match.group("old_len") is not None else 1
        new_len = int(match.group("new_len")) if match.group("new_len") is not None else 1
        body: list[str] = []
        i += 1
        # Bound the body by the declared old/new line counts rather than by
        # scanning for a "@@"/"--- " marker line: a deleted/added line whose
        # *content* starts with "-- " or "@@ " (a SQL/Lua comment, a decorator
        # line) renders as "--- ..."/"@@+ ..." in the body and would
        # otherwise be misread as the next hunk/file header, truncating the
        # hunk silently.
        old_count = 0
        new_count = 0
        while i < len(lines):
            body_line = lines[i]
            if body_line == _NO_NEWLINE_MARKER:
                body.append(body_line)
                i += 1
                continue
            if old_count >= old_len and new_count >= new_len:
                break
            if body_line.startswith(" ") or body_line == "":
                old_count += 1
                new_count += 1
            elif body_line.startswith("-"):
                old_count += 1
            elif body_line.startswith("+"):
                new_count += 1
            else:
                break
            body.append(body_line)
            i += 1
        hunks.append({"old_start": old_start, "old_len": old_len, "body": body})

    if not hunks:
        raise PatchApplyError("No valid unified-diff hunks found.")
    return hunks


def apply_unified_diff(original: str, diff_text: str) -> str:
    hunks = _parse_hunks(diff_text)
    trailing_newline = original == "" or original.endswith("\n")
    src_lines = original.splitlines()

    result: list[str] = []
    cursor = 0

    for hunk in hunks:
        # A hunk with old_len == 0 is a pure insertion with nothing from
        # the old file in its body; per unified-diff convention its
        # `old_start` is already the 0-based insertion point (the line
        # count *before* which new lines go), not a 1-based line
        # reference — `@@ -0,0 +1 @@` means "insert at the very start".
        # Every other hunk uses a normal 1-based first-line reference.
        if hunk["old_len"] == 0:
            old_start_idx = hunk["old_start"]
        else:
            old_start_idx = hunk["old_start"] - 1
        if old_start_idx < cursor:
            raise PatchApplyError("Hunks overlap or are out of order.")
        if old_start_idx > len(src_lines):
            raise PatchApplyError(
                f"Hunk starts at line {hunk['old_start']}, past end of file "
                f"({len(src_lines)} lines)."
            )

        result.extend(src_lines[cursor:old_start_idx])
        pos = old_start_idx

        for body_line in hunk["body"]:
            if body_line == _NO_NEWLINE_MARKER:
                continue
            if body_line.startswith(" "):
                expected = body_line[1:]
                _check_match(src_lines, pos, expected)
                result.append(expected)
                pos += 1
            elif body_line.startswith("-"):
                expected = body_line[1:]
                _check_match(src_lines, pos, expected)
                pos += 1
            elif body_line.startswith("+"):
                result.append(body_line[1:])
            elif body_line == "":
                _check_match(src_lines, pos, "")
                result.append("")
                pos += 1
            else:
                raise PatchApplyError(f"Unrecognized diff line: {body_line!r}")

        cursor = pos

    result.extend(src_lines[cursor:])
    new_text = "\n".join(result)
    if trailing_newline:
        new_text += "\n"
    return new_text


def _check_match(src_lines: list[str], pos: int, expected: str) -> None:
    actual = src_lines[pos] if pos < len(src_lines) else "<EOF>"
    if pos >= len(src_lines) or src_lines[pos] != expected:
        raise PatchApplyError(
            f"Context mismatch at line {pos + 1}: expected {expected!r}, got {actual!r}"
        )
