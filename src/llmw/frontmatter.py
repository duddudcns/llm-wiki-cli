"""YAML frontmatter extraction for wiki pages."""

from __future__ import annotations

import re

import yaml

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

_REPAIRABLE_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<key>[A-Za-z0-9_.-]+):[ \t]+(?P<value>.+)$"
)


class InvalidFrontmatterError(ValueError):
    pass


def _repair_unquoted_colon_values(raw_yaml: str) -> str | None:
    """Quote scalar values containing a bare ': ' (e.g. `summary: a: b`).

    Real-world wiki frontmatter often has free-text values with embedded
    colons, which PyYAML rejects as "mapping values are not allowed here".
    Returns the repaired YAML text, or None if no line qualified for repair.
    """
    repaired_any = False
    out_lines = []
    for line in raw_yaml.splitlines():
        match = _REPAIRABLE_LINE_RE.match(line)
        if match is None:
            out_lines.append(line)
            continue
        value = match.group("value")
        stripped = value.strip()
        if not stripped or stripped[0] in "\"'[{" or ": " not in value:
            out_lines.append(line)
            continue
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        out_lines.append(f'{match.group("indent")}{match.group("key")}: "{escaped}"')
        repaired_any = True
    if not repaired_any:
        return None
    return "\n".join(out_lines)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split `text` into (frontmatter_dict, body). Returns ({}, text) if absent.

    Raises InvalidFrontmatterError if a frontmatter block is present but is
    not valid YAML, or does not parse to a mapping.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw_yaml = match.group(1)
    body = text[match.end() :]

    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        data = None
        repaired = _repair_unquoted_colon_values(raw_yaml)
        if repaired is not None:
            try:
                data = yaml.safe_load(repaired)
            except yaml.YAMLError:
                data = None
        if data is None:
            # Report the original error, not the repaired attempt's.
            raise InvalidFrontmatterError(str(exc)) from exc

    if data is None:
        return {}, body
    if not isinstance(data, dict):
        raise InvalidFrontmatterError("frontmatter must be a YAML mapping")
    return data, body
