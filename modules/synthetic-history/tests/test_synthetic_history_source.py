# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""The Synthetic history source: the conformance every source passes, and what is its own."""

import time
from datetime import datetime, timedelta

import pytest

from pswamp_core.testing import SourceConformance
from pswamp_core.util.time import UTC
from pswamp_modules.synthetic_history import SyntheticHistory

T0 = datetime(2025, 10, 1, tzinfo=UTC)
#: Three seconds at 20 Hz with an outage that does not line up with frames:
#: [1.01 s, 1.53 s) holds the frames at 1.05 to 1.50 s.
SMALL = dict(start="2025-10-01T00:00:00Z", span=3, rate=20, outages=["2025-10-01T00:00:01.01Z/2025-10-01T00:00:01.53Z"])


def expected_timestamps(start: datetime, span_s: float, rate: int, outages: list[tuple[datetime, datetime]]) -> list[datetime]:
    """Every frame instant, by brute force: no index arithmetic."""
    step = timedelta(microseconds=1_000_000 // rate)
    instants, t = [], start
    while t < start + timedelta(seconds=span_s):
        if not any(a <= t < b for a, b in outages):
            instants.append(t)
        t += step
    return instants


class TestSyntheticHistory(SourceConformance):
    @pytest.fixture
    def source_under_test(self):
        return SyntheticHistory(**SMALL)

    @pytest.fixture
    def conformance_records(self, source_under_test):
        outage = (T0 + timedelta(seconds=1.01), T0 + timedelta(seconds=1.53))
        return [source_under_test.frame_at(t) for t in expected_timestamps(T0, 3, 20, [outage])]


def test_the_outage_holds_no_frames():
    instants = [frame.timestamp for frame in SyntheticHistory(**SMALL).read()]
    assert len(instants) == 60 - 10
    assert T0 + timedelta(seconds=1.0) in instants and T0 + timedelta(seconds=1.55) in instants
    assert not any(T0 + timedelta(seconds=1.01) <= t < T0 + timedelta(seconds=1.53) for t in instants)


def test_a_read_from_inside_an_outage_starts_after_it():
    first = next(SyntheticHistory(**SMALL).read(T0 + timedelta(seconds=1.2)))
    assert first.timestamp == T0 + timedelta(seconds=1.55)


def test_a_year_is_read_from_any_instant_at_once():
    source = SyntheticHistory()
    assert source.coverage() == source.coverage()  # computed, not stored
    target = datetime(2026, 3, 14, 13, 5, 0, 30_000, tzinfo=UTC)
    began = time.perf_counter()
    frames = source.read(target)
    first, second = next(frames), next(frames)
    assert time.perf_counter() - began < 0.1
    assert first.timestamp == datetime(2026, 3, 14, 13, 5, 0, 50_000, tzinfo=UTC)
    assert second.timestamp - first.timestamp == timedelta(milliseconds=50)
    assert len(first.values) == 15 and first.header.data_rate == 20.0


def test_the_default_outages_are_holes():
    source = SyntheticHistory()
    assert next(source.read(datetime(2025, 10, 1, 0, 0, 11, tzinfo=UTC))).timestamp == datetime(
        2025, 10, 1, 0, 0, 12, 500_000, tzinfo=UTC
    )
    assert next(source.read(datetime(2026, 1, 10, tzinfo=UTC))).timestamp == datetime(2026, 1, 13, tzinfo=UTC)


def test_outages_at_the_edges_move_the_coverage():
    source = SyntheticHistory(
        start="2025-10-01T00:00:00Z",
        span=3,
        outages=["2025-09-30T00:00:00Z/2025-10-01T00:00:00.5Z", "2025-10-01T00:00:02.5Z/2025-10-02T00:00:00Z"],
    )
    coverage = source.coverage()
    assert coverage.start == T0 + timedelta(seconds=0.5)
    assert coverage.end == T0 + timedelta(seconds=2.5)  # the last frame, at 2.45 s, plus one interval


def test_a_source_that_is_all_outage_holds_nothing():
    assert SyntheticHistory(span=1, outages=["2025-09-01T00:00:00Z/2025-11-01T00:00:00Z"]).coverage() is None


def test_two_instances_agree():
    a, b = SyntheticHistory(**SMALL), SyntheticHistory(**SMALL)
    assert [f.model_dump() for f in a.read()] == [f.model_dump() for f in b.read()]


def test_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("HISTORY_START", "2024-01-01T00:00:00Z")
    monkeypatch.setenv("HISTORY_SPAN", "60")
    monkeypatch.setenv("HISTORY_RATE", "50")
    monkeypatch.setenv("HISTORY_OUTAGES", "2024-01-01T00:00:10Z/2024-01-01T00:00:20Z")
    source = SyntheticHistory.from_env("history")
    assert source.coverage() == source.coverage()
    assert len(list(source.read())) == 50 * 50


@pytest.mark.parametrize(
    "settings",
    [
        dict(rate=7),  # 1e6 / 7 is not a whole microsecond
        dict(rate=0),
        dict(start="yesterday"),
        dict(span=0),
        dict(outages=["2025-10-01T00:00:00Z"]),
        dict(outages=["2025-10-02T00:00:00Z/2025-10-01T00:00:00Z"]),
    ],
)
def test_bad_settings_are_refused(settings):
    with pytest.raises(ValueError):
        SyntheticHistory(**settings)


def test_it_is_a_playable_history():
    assert SyntheticHistory.kind == "history"
    assert SyntheticHistory.commands
