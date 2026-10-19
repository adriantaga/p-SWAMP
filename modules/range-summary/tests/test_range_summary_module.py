"""The range summary module: a batch query answered from the module's own sources.

The set of sources is built here, over two small in-memory sources (a recording
and a live feed), so the test needs nothing but the core and the models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pswamp_core.command_routing import CommandRefused
from pswamp_core.sources import SourceModule, SourceSet
from pswamp_core.time_range import TimeRange
from pswamp_models.pmu import PmuFrame, PmuHeader
from pswamp_models.range_summary import RangeSummaryResult, SummarizeRangeCommand
from pswamp_modules.range_summary import RangeSummaryModule

RATE_HZ = 20.0
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
HEADER = PmuHeader(
    station=["A", "A", "B", "B"],
    channel=["V", "f", "V", "f"],
    measurement=["V_Magnitude", "f", "V_Magnitude", "f"],
    units=["kV", "Hz", "kV", "Hz"],
    data_rate=RATE_HZ,
)


def frame(t: float) -> PmuFrame:
    """A frame ``t`` s in: the frequency ramps up 4 mHz/s from 50 Hz."""
    f = 50.0 + 0.004 * t
    return PmuFrame(timestamp=T0 + timedelta(seconds=t), mRID="ramp", header=HEADER, values=[400.0, f, 400.0, f])


class Recording(SourceModule):
    """Three seconds of the ramp, as a history."""

    name = "test-recording"
    kind = "history"

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self.frames = [frame(n / RATE_HZ) for n in range(int(3 * RATE_HZ))]

    def coverage(self) -> TimeRange:
        return TimeRange(self.frames[0].timestamp, self.frames[-1].timestamp + timedelta(seconds=1 / RATE_HZ))

    def read(self, start=None, end=None):
        for record in self.frames:
            if TimeRange(start, end).contains(record.timestamp):
                yield record


class Feed(SourceModule):
    """A live feed: the module refuses to summarize it."""

    name = "test-feed"
    kind = "live"
    blocking = True  # a live feed written as read waits for its records

    def read(self, start=None, end=None):
        yield frame(0)


def sources() -> SourceSet:
    return SourceSet([Recording("sample"), Feed("live")])


def summarize(source: str, start: float, end: float) -> SummarizeRangeCommand:
    """``[start, end)`` seconds after ``T0``."""
    return SummarizeRangeCommand(source=source, start=T0 + timedelta(seconds=start), end=T0 + timedelta(seconds=end))


async def test_the_range_summary_reads_its_own_sources():
    module = RangeSummaryModule()
    module.sources = sources()
    command = summarize("sample", 1.0, 2.0)
    (answer,) = await module.arun_command(command)
    assert isinstance(answer, RangeSummaryResult) and answer.request_id == command.request_id
    summary = answer.result
    assert summary.frames == 20 and summary.max_frequency_hz > 50.0075
    assert (summary.start, summary.end) == (T0 + timedelta(seconds=1), T0 + timedelta(seconds=2))
    assert summary.min_frequency_hz == pytest.approx(50.004) and summary.mean_frequency_hz == pytest.approx(50.0059)
    for refused in (summarize("live", 0, 1), summarize("nope", 0, 1), summarize("sample", 2, 1)):
        with pytest.raises(CommandRefused):
            module.validate(refused)
    with pytest.raises(CommandRefused, match="nothing"):
        await module.ahandle(summarize("sample", 10, 11))


def test_an_instant_without_a_zone_is_utc():
    naive = SummarizeRangeCommand(source="sample", start=datetime(2026, 1, 1, 0, 0, 1), end=datetime(2026, 1, 1, 0, 0, 2))
    assert naive.start == T0 + timedelta(seconds=1) and naive.start.tzinfo is not None


def test_the_range_summary_answers_from_plain_code():
    module = RangeSummaryModule()
    module.sources = sources()
    (answer,) = module.run_command(summarize("sample", 0.0, 1.0))
    assert answer.result.frames == 20
