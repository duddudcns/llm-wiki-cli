"""How old is this page's claim? — shared formatting for search/read.

A page recording *mechanism* (the real A→B→C chain, with file and function
names) is the most useful thing in a wiki and the first thing to rot when
the code moves. What costs something is not the rotting; it is reading a
rotted page as current. So both read-side surfaces print an age.

Two dates are available and they mean different things. `updated` is the
page's own claim about when its content was last restated — agent-asserted,
and therefore the one that means "verified". `body_changed_at` is when the
index last *observed* the page's body change. Neither is a substitute for
the other, so when they disagree this prints both rather than quietly
preferring one: that gap means somebody edited the body and left the claim
behind, which is exactly the state worth being suspicious of.

Deliberately the body, not the file. Declaring `code:`, marking a page
superseded, or fixing a tag rewrites the file without restating any claim,
and the write-side rule says correctly not to bump `updated` for those. A
file-based signal would therefore fire forever on every page any metadata
edit ever touched — one `code:` sweep did exactly that to 21 of this
project's own 31 pages before the basis was moved here.

Deliberately not done here: bumping `updated` on the caller's behalf. That
would make a typo fix look like a re-verification — an error in the
fresh-ward direction, which is the direction that produces wrong
judgments. A freshness display should fail toward distrust.
"""

from __future__ import annotations

import datetime

# Both dates have day resolution, and a page written and restated in the
# same session lands on the same day. Only a gap wider than a day says
# anything.
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


def _age(days: int) -> str:
    if days == 0:
        return "today"
    return f"{days}d ago"


def describe(
    updated: object,
    body_changed_at: object = None,
    today: datetime.date | None = None,
) -> str | None:
    """Render the freshness suffix for one page, or None when there is
    nothing to say. Never raises on malformed input: an unparseable
    `updated` is still shown verbatim, since the agent can read a typo but
    cannot read a field we swallowed."""
    today = today or datetime.date.today()
    claimed = as_date(updated)
    modified = as_date(body_changed_at)

    if claimed is None:
        # Present but not a date we understand — pass it through, since
        # the agent can read a typo but not a field we swallowed.
        # Absent entirely: say nothing. "unknown (body changed X)" answers
        # a question nobody asked and reads like a warning, and an
        # `llmw archive` tombstone — no `updated`, no content but a
        # redirect — would carry it on every search. A missing `updated`
        # is reported by `llmw lint` and by the writer at write time.
        return str(updated) if updated else None

    notes = []
    age_days = (today - claimed).days
    if age_days >= 0:
        notes.append(_age(age_days))
    if modified is not None and (modified - claimed).days > _DIVERGENCE_DAYS:
        notes.append(f"body changed {modified.isoformat()}")

    if not notes:
        return claimed.isoformat()
    return f"{claimed.isoformat()} ({', '.join(notes)})"
