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
        body: list[str] = []
        i += 1
        while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- "):
            body.append(lines[i])
            i += 1
        hunks.append({"old_start": old_start, "body": body})

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
