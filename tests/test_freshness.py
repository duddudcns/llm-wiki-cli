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


def _observed(year: int, month: int, day: int) -> str:
    """A `body_changed_at` stamp: the day the index last saw this page's
    body change. Stored as an ISO date string, like `updated`."""
    return datetime.date(year, month, day).isoformat()


def test_claim_alone_reports_its_age() -> None:
    assert describe("2026-07-13", None, today=TODAY) == "2026-07-13 (49d ago)"


def test_a_claim_restated_today_reads_as_today() -> None:
    assert describe("2026-08-31", None, today=TODAY) == "2026-08-31 (today)"


def test_a_body_change_after_the_claim_shows_both() -> None:
    # The gap is the signal: the body moved and the claim did not.
    assert describe("2026-07-13", _observed(2026, 8, 31), today=TODAY) == (
        "2026-07-13 (49d ago, body changed 2026-08-31)"
    )


def test_a_body_change_on_the_same_day_is_not_divergence() -> None:
    # A page written and restated in one session lands on the same day, so
    # a same-day stamp must stay quiet or the notice fires on everything.
    assert describe("2026-08-31", _observed(2026, 8, 31), today=TODAY) == (
        "2026-08-31 (today)"
    )


@pytest.mark.parametrize(
    ("observed_day", "expected_note"),
    [(1, False), (2, True)],
)
def test_divergence_needs_more_than_a_day_of_gap(
    observed_day: int, expected_note: bool
) -> None:
    # The boundary itself: both dates have day resolution and a page
    # restated the day after an edit is not evidence of anything. Two days
    # means somebody came back and changed the body.
    result = describe("2026-08-01", _observed(2026, 8, 1 + observed_day), today=TODAY)
    assert ("body changed" in result) is expected_note


def test_a_body_change_older_than_the_claim_is_not_divergence() -> None:
    # Wrong in the harmless direction: the claim is newer than the last
    # observed body change, which is the state we want.
    assert describe("2026-08-31", _observed(2026, 7, 1), today=TODAY) == (
        "2026-08-31 (today)"
    )


def test_a_claim_in_the_future_drops_the_age_but_keeps_the_date() -> None:
    # "-12d ago" is worse than no age at all, but the date itself is still
    # something the reader can judge.
    assert describe("2026-09-12", None, today=TODAY) == "2026-09-12"


def test_a_page_that_makes_no_claim_gets_no_freshness_line() -> None:
    # "unknown (body changed X)" answers a question nobody asked and reads
    # like a warning. An `llmw archive` tombstone carries no `updated` and
    # no content but "see elsewhere", so it hit this on every search. The
    # missing field is reported where it belongs: `llmw lint`, and the
    # writer's own notice at the moment of writing.
    assert describe(None, _observed(2026, 8, 31), today=TODAY) is None


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
    result = describe(value, _observed(2026, 8, 31), today=TODAY)
    assert result == str(value)


def test_a_datetime_stamped_claim_keeps_its_date_half() -> None:
    # Some wikis write `updated: 2026-07-13T09:30:00`; that is a date we
    # understand, not a malformed one.
    assert describe("2026-07-13T09:30:00", None, today=TODAY) == (
        "2026-07-13 (49d ago)"
    )


def test_an_unusable_observation_does_not_crash_the_line() -> None:
    assert describe("2026-07-13", "last tuesday", today=TODAY) == "2026-07-13 (49d ago)"
