# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""``SyntheticHistory``: months of PMU frames, computed rather than stored.

A stand-in for a long-term store: ``SPAN`` of frames from ``START`` at
``RATE`` Hz, five stations, holding nothing inside ``OUTAGES``. Every frame is
a function of its instant, so a read from any instant starts there at once and
a year costs no memory::

    source = SyntheticHistory()
    source.coverage()                                   # [first frame, last + one interval)
    next(source.read(datetime(2026, 3, 14, 13, 5, tzinfo=UTC)))

Settings (``{SOURCE}_{SETTING}``, or keywords in a script):

- ``START``: the first instant, ISO 8601 (``2025-10-01T00:00:00Z``).
- ``SPAN``: seconds of data from there (a year).
- ``RATE``: frames per second; it must divide 1 000 000, so every timestamp
  is a whole microsecond.
- ``OUTAGES``: comma-separated ``<iso start>/<iso end>`` ranges, half-open,
  with no frames.

Timestamps are counted in whole microseconds from ``START``, so a seek lands on
the exact frame and two instances agree to the microsecond.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Iterator, Sequence
from datetime import datetime, timedelta
from typing import Any

from pswamp_core.playable import Playable
from pswamp_core.settings import EnvSetting
from pswamp_core.sources import SourceModule
from pswamp_core.time_range import TimeRange
from pswamp_core.util.time import ensure_utc
from pswamp_models.pmu import PmuFrame, PmuHeader

__all__ = ["DEFAULT_OUTAGES", "STATIONS", "STREAM_ID", "SyntheticHistory"]

#: The five stations of the sample recording, with their nominal voltage (kV)
#: and angle (deg).
STATIONS: tuple[tuple[str, float, float], ...] = (
    ("3000", 420.0, 0.0),
    ("3245", 420.0, 7.1),
    ("5100", 300.0, 7.3),
    ("6500", 420.0, -12.0),
    ("7000", 420.0, -4.5),
)
_MEASUREMENTS = (("V", "V_Magnitude", "kV"), ("V", "V_Angle", "deg"), ("f", "f", "Hz"))

#: The mRID every frame carries.
STREAM_ID = "synthetic-history"

#: A 2.5 s dropout ten seconds in, a 15 min outage, and a 3-day outage.
DEFAULT_OUTAGES = (
    "2025-10-01T00:00:10.025Z/2025-10-01T00:00:12.5Z,"
    "2025-11-03T12:00:00Z/2025-11-03T12:15:00Z,"
    "2026-01-10T00:00:00Z/2026-01-13T00:00:00Z"
)

_US = timedelta(microseconds=1)


class SyntheticHistory(Playable, SourceModule):
    """A long synthetic history with outages. See the module docstring."""

    name = "synthetic-history"
    kind = "history"
    outputs = (PmuFrame,)
    env_settings = (
        EnvSetting("START", "The first instant, ISO 8601", default="2025-10-01T00:00:00Z"),
        EnvSetting("SPAN", "Seconds of data from START", default=str(365 * 86400), kind="seconds"),
        EnvSetting("RATE", "Frames per second; must divide 1000000", default="20", kind="int"),
        EnvSetting("OUTAGES", "Comma-separated <iso start>/<iso end> ranges with no frames", default=DEFAULT_OUTAGES, kind="list"),
    )

    def __init__(self, source: str | None = None, **settings: Any) -> None:
        super().__init__(source, **settings)
        self.start: datetime = _instant(self.settings.start, "START")
        rate = self.settings.rate
        if not isinstance(rate, int) or rate <= 0 or 1_000_000 % rate:
            raise ValueError(f"{type(self).__name__}: RATE must be a whole number of Hz dividing 1000000, not {rate!r}")
        span_us = self.settings.span // _US
        if span_us <= 0:
            raise ValueError(f"{type(self).__name__}: SPAN must be positive, not {self.settings.span}")
        self.step_us = 1_000_000 // rate
        #: Frames ``k`` in ``[0, slots)`` sit at ``start + k * step_us``.
        self.slots = _ceil_div(span_us, self.step_us)
        #: The outages as frame-index ranges ``[a, b)``, sorted and merged.
        self.outages = _index_ranges(self.settings.outages or [], self.start, self.step_us)
        self._outage_ends = [b for _, b in self.outages]
        self.header = PmuHeader(
            station=[name for name, _, _ in STATIONS for _ in _MEASUREMENTS],
            channel=[channel for _ in STATIONS for channel, _, _ in _MEASUREMENTS],
            measurement=[measurement for _ in STATIONS for _, measurement, _ in _MEASUREMENTS],
            units=[unit for _ in STATIONS for _, _, unit in _MEASUREMENTS],
            data_rate=float(rate),
        )

    # -- the source ------------------------------------------------------------------

    def coverage(self) -> TimeRange | None:
        first = self._next_held(0, self.slots)
        last = self._last_held()
        if first is None or last is None:
            return None
        return TimeRange(self._at(first), self._at(last + 1))

    def read(self, start: datetime | None = None, end: datetime | None = None) -> Iterator[PmuFrame]:
        k = 0 if start is None else max(0, _ceil_div(self._us(start), self.step_us))
        stop = self.slots if end is None else min(self.slots, max(0, _ceil_div(self._us(end), self.step_us)))
        i = bisect.bisect_right(self._outage_ends, k)  # the first outage ending after k
        while k < stop:
            if i < len(self.outages) and self.outages[i][0] <= k:
                k, i = self.outages[i][1], i + 1
                continue
            limit = min(stop, self.outages[i][0]) if i < len(self.outages) else stop
            for index in range(k, limit):
                yield self.frame_at(self._at(index))
            k = limit

    # -- the data --------------------------------------------------------------------

    def frame_at(self, timestamp: datetime) -> PmuFrame:
        """The frame this source would hold at ``timestamp``: slow swings in
        frequency, voltage and angle, a phase apart per station."""
        t = (timestamp - self.start) / _US / 1e6
        values: list[float | None] = []
        for n, (_, kv, angle) in enumerate(STATIONS):
            values.append(kv * (1 + 0.01 * math.sin(2 * math.pi * t / 3600 + n)))
            values.append(angle + 2.0 * math.sin(2 * math.pi * t / 600 + n))
            values.append(
                50.0 + 0.02 * math.sin(2 * math.pi * t / 86400) + 0.01 * math.sin(2 * math.pi * t / 37 + n) + 0.0005 * n
            )
        return PmuFrame(timestamp=timestamp, mRID=STREAM_ID, header=self.header, values=values)

    # -- frame indices ---------------------------------------------------------------

    def _at(self, k: int) -> datetime:
        return self.start + k * self.step_us * _US

    def _us(self, moment: datetime) -> int:
        return (ensure_utc(moment) - self.start) // _US

    def _next_held(self, k: int, stop: int) -> int | None:
        """The first index at or after ``k``, below ``stop``, not in an outage."""
        i = bisect.bisect_right(self._outage_ends, k)
        if i < len(self.outages) and self.outages[i][0] <= k:
            k = self.outages[i][1]
        return k if k < stop else None

    def _last_held(self) -> int | None:
        k = self.slots - 1
        i = bisect.bisect_right(self._outage_ends, k)
        if i < len(self.outages) and self.outages[i][0] <= k:
            k = self.outages[i][0] - 1
        return k if k >= 0 else None


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


def _instant(value: Any, setting: str) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(datetime.fromisoformat(str(value)))
    except ValueError:
        raise ValueError(f"SyntheticHistory: {setting} must be an ISO 8601 instant, not {value!r}") from None


def _index_ranges(outages: Sequence[Any], start: datetime, step_us: int) -> list[tuple[int, int]]:
    """``<iso start>/<iso end>`` strings (or pairs of datetimes) as merged,
    sorted frame-index ranges ``[a, b)``: the frames at ``a`` to ``b - 1``
    are the ones inside the outage."""
    ranges: list[tuple[int, int]] = []
    for outage in outages:
        if isinstance(outage, str):
            first, sep, last = outage.partition("/")
            if not sep:
                raise ValueError(f"SyntheticHistory: an outage is <iso start>/<iso end>, not {outage!r}")
        else:
            first, last = outage
        a, b = _instant(first, "OUTAGES"), _instant(last, "OUTAGES")
        if b <= a:
            raise ValueError(f"SyntheticHistory: outage {outage!r} ends before it starts")
        ranges.append((max(0, _ceil_div((a - start) // _US, step_us)), max(0, _ceil_div((b - start) // _US, step_us))))
    merged: list[tuple[int, int]] = []
    for a, b in sorted(ranges):
        if a >= b:
            continue  # between two frames: nothing missing
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged
