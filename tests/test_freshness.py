"""Edge cases for the freshness formatter.

`describe` runs on every search result and every `read --brief`, over
frontmatter an agent hand-wrote. It must never raise, and it must never
silently swallow a field the reader could have interpreted themselves.
"""

from __future__ import annotations

import datetime

import pytest

from llmw.freshness import describe

TODAY = datetime.date(2026, 8, 31)


def _mtime(year: int, month: int, day: int) -> float:
    return datetime.datetime(year, month, day, 12, 0).timestamp()


def test_claim_alone_reports_its_age() -> None:
    assert describe("2026-07-13", None, today=TODAY) == "2026-07-13 (49d ago)"


def test_a_claim_restated_today_reads_as_today() -> None:
    assert describe("2026-08-31", None, today=TODAY) == "2026-08-31 (today)"


def test_a_file_newer_than_its_claim_shows_both() -> None:
    # The gap is the signal: the body moved and the claim did not.
    assert describe("2026-07-13", _mtime(2026, 8, 31), today=TODAY) == (
        "2026-07-13 (49d ago, file modified 2026-08-31)"
    )


def test_a_file_touched_the_same_day_is_not_divergence() -> None:
    # Every page is written to disk moments after its `updated` is set, so
    # a same-day mtime must stay quiet or the notice fires on everything.
    assert describe("2026-08-31", _mtime(2026, 8, 31), today=TODAY) == (
        "2026-08-31 (today)"
    )


def test_a_file_older_than_its_claim_is_not_divergence() -> None:
    # Backdated only in the harmless direction — a `git checkout` resets
    # mtimes without touching content.
    assert describe("2026-08-31", _mtime(2026, 7, 1), today=TODAY) == (
        "2026-08-31 (today)"
    )


def test_a_claim_in_the_future_drops_the_age_but_keeps_the_date() -> None:
    # "-12d ago" is worse than no age at all, but the date itself is still
    # something the reader can judge.
    assert describe("2026-09-12", None, today=TODAY) == "2026-09-12"


def test_a_missing_claim_falls_back_to_the_file_and_says_so() -> None:
    # Labelled as a filesystem fact, never dressed up as a verification
    # date the page never made.
    assert describe(None, _mtime(2026, 8, 31), today=TODAY) == (
        "unknown (file modified 2026-08-31)"
    )


def test_nothing_at_all_yields_nothing() -> None:
    assert describe(None, None, today=TODAY) is None


def test_an_unquoted_yaml_date_is_read_as_the_date_it_is() -> None:
    # `updated: 2026-07-13` without quotes reaches us as the int 20260713,
    # which is compact ISO 8601 and means exactly what it looks like.
    assert describe(20260713, None, today=TODAY) == "2026-07-13 (49d ago)"


@pytest.mark.parametrize(
    "value",
    ["last tuesday", "2026-13-45", {"nested": "mapping"}],
)
def test_an_uninterpretable_claim_is_passed_through_verbatim(value: object) -> None:
    # An agent can read a malformed date and act on it; it cannot read a
    # field we dropped. Whatever it is, show it.
    result = describe(value, _mtime(2026, 8, 31), today=TODAY)
    assert result == str(value)


def test_a_datetime_stamped_claim_keeps_its_date_half() -> None:
    # Some wikis write `updated: 2026-07-13T09:30:00`; that is a date we
    # understand, not a malformed one.
    assert describe("2026-07-13T09:30:00", None, today=TODAY) == (
        "2026-07-13 (49d ago)"
    )


def test_an_unusable_mtime_does_not_crash_the_line() -> None:
    assert describe("2026-07-13", 10.0**20, today=TODAY) == "2026-07-13 (49d ago)"
