# range-summary

`pswamp-range-summary`, package `pswamp_modules.range_summary`, class
`RangeSummaryModule`, entry point `range-summary` (group `pswamp.modules`).

A batch query: asked about `[start, end)` of a recording (UTC instants), it
reads that range from its own sources (a `SourceSet`) and answers with the frame
count and the min, max and mean frequency over it. It keeps running totals, not
the values, so a long range costs time and not memory.

| | Message | Topic | Defined in |
|---|---|---|---|
| Reads | no topic (`inputs = ()`); it reads its sources (`reads_sources = True`) | | |
| Emits | `RangeSummaryResult` (body `RangeSummary`), carrying the command's `request_id` | `range.summary.result` | `pswamp_models.range_summary` |
| Accepts | `SummarizeRangeCommand(source, start, end)` | `summarize.range.command` | `pswamp_models.range_summary` |

**Parameters:** none. A command is refused (`CommandRefused`, which the host
publishes as an `ErrorEvent`) when the source is unknown, is live rather than
history, the range is empty, or the range holds no frame. Reading the sources
awaits, so the module answers in `ahandle`; hosted, it can run in a worker of
its own (`batch-worker` in `docker-compose.yml`).

## From a script

The module needs its sources, set by its host or by hand. `run_command` runs the
async handler on a loop of its own, so the script stays synchronous.

```python
from datetime import datetime, timedelta, timezone

from pswamp_models.range_summary import SummarizeRangeCommand
from pswamp_modules.range_summary import RangeSummaryModule

summary = RangeSummaryModule()
summary.sources = sources                  # a pswamp_core SourceSet with a history source
t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
(answer,) = summary.run_command(SummarizeRangeCommand(source="sample", start=t0, end=t0 + timedelta(seconds=1)))
answer.result.mean_frequency_hz
```

## Examples

`examples/summarize_range.py` gives the module its sources over a small synthetic
recording (a minimal in-memory `SourceModule`) and summarizes four ranges of it:

    uv run python modules/range-summary/examples/summarize_range.py

## Tests

`uv run pswamp test module range-summary` (also part of `uv run pswamp test server`).
