"""YAML frontmatter extraction for wiki pages."""

from __future__ import annotations

import re

import yaml

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


class InvalidFrontmatterError(ValueError):
    pass


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
        raise InvalidFrontmatterError(str(exc)) from exc

    if data is None:
        return {}, body
    if not isinstance(data, dict):
        raise InvalidFrontmatterError("frontmatter must be a YAML mapping")
    return data, body
