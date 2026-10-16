# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""``RangeSummaryModule``: a batch query, answered by a module reading the sources.

It reads no topic (``inputs = ()``) and only answers
``SummarizeRangeCommand``: it reads ``[start, end)`` of a recording from its
own ``SourceSet`` (``reads_sources``) and publishes a summary, keeping running
totals rather than the values, so a long range costs time and not memory.
Reading the sources awaits, so it answers in ``ahandle`` rather than
``handle``; from a script, ``run_command`` runs that on a loop of its own.
It runs wherever its host runs; in compose, in a worker of its own. A range
it cannot summarize (a live source, nothing in the range) is refused, and the
refusal comes back as an ``ErrorEvent``. Its messages are in
``pswamp_models.range_summary``.
"""

from __future__ import annotations

from pswamp_core.command_routing import CommandRefused
from pswamp_core.modules import Module
from pswamp_models.pmu import PmuFrame
from pswamp_models.range_summary import RangeSummary, RangeSummaryResult, SummarizeRangeCommand

__all__ = ["RangeSummaryModule"]


class RangeSummaryModule(Module):
    name = "range-summary"
    outputs = (RangeSummaryResult,)
    commands = (SummarizeRangeCommand,)
    reads_sources = True

    def validate(self, command: SummarizeRangeCommand) -> None:
        if command.source not in self.sources.sources:
            raise CommandRefused(f"no source named {command.source!r}")
        if self.sources.kind(command.source) != "history":
            raise CommandRefused(f"{command.source} is live: there is no range to summarize")
        if command.end <= command.start:
            raise CommandRefused("the range is empty")

    async def ahandle(self, command: SummarizeRangeCommand) -> RangeSummary:
        self.sources.switch(command.source)
        frames, count, total, low, high = 0, 0, 0.0, float("inf"), float("-inf")
        async for frame in await self.sources.consume(command.start, command.end):
            if isinstance(frame, PmuFrame):
                frames += 1
                for i in frame.header.columns(measurement="f"):
                    value = frame.values[i]
                    if value is not None:
                        count, total, low, high = count + 1, total + value, min(low, value), max(high, value)
        if not count:
            raise CommandRefused(
                f"{command.source} holds nothing in [{command.start.isoformat()}, {command.end.isoformat()})"
            )
        return RangeSummary(
            source=command.source,
            start=command.start,
            end=command.end,
            frames=frames,
            min_frequency_hz=low,
            max_frequency_hz=high,
            mean_frequency_hz=total / count,
        )
