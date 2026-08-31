"""How old is this page's claim? — shared formatting for search/read.

A page recording *mechanism* (the real A→B→C chain, with file and function
names) is the most useful thing in a wiki and the first thing to rot when
the code moves. What costs something is not the rotting; it is reading a
rotted page as current. So both read-side surfaces print an age.

Two dates are available and they mean different things. `updated` is the
page's own claim about when its content was last restated — agent-asserted,
and therefore the one that means "verified". `mtime` is a filesystem fact:
when the bytes last changed. Neither is a substitute for the other, so
when they disagree this prints both rather than quietly preferring one:
that gap means somebody edited the body and left the claim behind, which
is exactly the state worth being suspicious of.

Deliberately not done here: bumping `updated` on the caller's behalf. That
would make a typo fix look like a re-verification — an error in the
fresh-ward direction, which is the direction that produces wrong
judgments. A freshness display should fail toward distrust.
"""

from __future__ import annotations

import datetime

# A page written and indexed in one session has an mtime seconds newer
# than its `updated` date, and `updated` has only day resolution. Only a
# gap wider than a day says anything.
_DIVERGENCE_DAYS = 1


def as_date(value: object) -> datetime.date | None:
    """The date a frontmatter value means, or None if it isn't one.

    Frontmatter reaches the index as text and legitimately arrives in
    three shapes: `2026-07-13`, `20260713` (an unquoted YAML integer,
    which is compact ISO 8601 for the same day), and
    `2026-07-13T09:30:00`. Anything comparing or ordering these has to go
    through here — comparing them as strings puts every compact date
    above every hyphenated one, since `-` is 0x2D and `0` is 0x30.
    """
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


_parse_iso_date = as_date


def _mtime_date(mtime: float | None) -> datetime.date | None:
    if not mtime:
        return None
    try:
        return datetime.datetime.fromtimestamp(mtime).date()
    except (OSError, OverflowError, ValueError):
        return None


def _age(days: int) -> str:
    if days == 0:
        return "today"
    return f"{days}d ago"


def describe(
    updated: object,
    mtime: float | None = None,
    today: datetime.date | None = None,
) -> str | None:
    """Render the freshness suffix for one page, or None when there is
    nothing to say. Never raises on malformed input: an unparseable
    `updated` is still shown verbatim, since the agent can read a typo but
    cannot read a field we swallowed."""
    today = today or datetime.date.today()
    claimed = _parse_iso_date(updated)
    modified = _mtime_date(mtime)

    if claimed is None:
        if updated:
            # Present but not a date we understand — pass it through.
            return str(updated)
        if modified is None:
            return None
        return f"unknown (file modified {modified.isoformat()})"

    notes = []
    age_days = (today - claimed).days
    if age_days >= 0:
        notes.append(_age(age_days))
    if modified is not None and (modified - claimed).days > _DIVERGENCE_DAYS:
        notes.append(f"file modified {modified.isoformat()}")

    if not notes:
        return claimed.isoformat()
    return f"{claimed.isoformat()} ({', '.join(notes)})"
