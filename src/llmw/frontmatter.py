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


# A project can override which frontmatter keys are required via
# `.llmw/config.toml`'s `[lint] required_frontmatter` (see config.py).
# "updated" is additionally satisfied by a `last_updated` key, a common
# synonym in wikis that don't track created/updated separately.
FIELD_SYNONYMS = {"updated": ("last_updated",)}


def has_field(frontmatter: dict, field_name: str) -> bool:
    if frontmatter.get(field_name):
        return True
    return any(frontmatter.get(syn) for syn in FIELD_SYNONYMS.get(field_name, ()))


def missing_fields(frontmatter: dict, required: list[str]) -> list[str]:
    """Which of `required` this frontmatter does not satisfy. Shared by
    `llmw lint` and the writer's post-write notice, so a page cannot pass
    one and fail the other."""
    return [name for name in required if not has_field(frontmatter, name)]


def set_fields(text: str, fields: dict) -> str:
    """Return `text` with `fields` set in its frontmatter.

    When every key is new and the block parses, the new lines are appended
    to it and nothing else is touched — key order, quoting, and comments
    survive byte-for-byte. When a key must be *replaced*, the mapping is
    re-dumped and the block is normalized.

    In practice the append path's customer is `write_page` injecting
    `supersedes:` into content the caller just handed it. The supersede
    flip and archive both set `status`, which every real page already has,
    so they take the re-dump path — do not read the byte-preservation
    promise as protecting a hand-authored page from being normalized.

    Re-dumping is why this belongs to lifecycle operations — archiving,
    superseding — where writing metadata is the entire point of the call.
    An ordinary edit must not reformat a page behind the author's back.
    """
    match = _FRONTMATTER_RE.match(text)
    try:
        data, body = split_frontmatter(text)
        parsed = True
    except InvalidFrontmatterError:
        # Two things go wrong here if handled naively.
        #
        # `body = text` is wrong: `text` is the whole file, delimiters
        # included, so the unreadable block gets re-emitted below the new
        # one and the page ends up carrying two.
        #
        # Appending to the block is wrong too, and worse, because it looks
        # right: the new keys land inside YAML that still doesn't parse,
        # so as *data* they do not exist. The indexer drops the page on
        # reparse, the mark never reaches search, backlinks, or the status
        # flag — and the command reports success over an inert operation.
        #
        # So: demote what could not be read into the body, visibly and
        # verbatim, and write a clean block. Nothing is lost, the result
        # parses, and the mark is real.
        data, parsed = {}, False
        body = text[match.end():] if match is not None else text
        if match is not None:
            body = (
                "\n```\n"
                "# frontmatter that could not be parsed, preserved verbatim\n"
                f"{match.group(1)}\n"
                "```\n" + body
            )

    pending = {k: v for k, v in fields.items() if data.get(k) != v}
    if not pending:
        return text

    if parsed and match is not None and not any(key in data for key in pending):
        added = yaml.safe_dump(pending, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{match.group(1)}\n{added}\n---\n{body}"

    merged = {**data, **fields}
    block = yaml.safe_dump(merged, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{block}\n---\n{body}"
