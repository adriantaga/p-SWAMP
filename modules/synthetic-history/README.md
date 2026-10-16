# synthetic-history

`pswamp-synthetic-history`, package `pswamp_modules.synthetic_history`, class
`SyntheticHistory`, entry point `synthetic-history` (group `pswamp.modules`).

A **source**: it has no inputs, it produces. A *history* a year deep, with
holes, that holds nothing on disk: every frame is computed from its instant.
It stands in for a long-term store. The remote data stub serves it in compose
and k8s, so the `remote` source behaves like the real one. It is *playable*:
the player controls apply.

| | Message | Topic | Defined in |
|---|---|---|---|
| Reads | nothing | | |
| Emits | `PmuFrame` (the primary, paced stream) | `pmu.frame` | `pswamp_models.pmu` |
| Accepts | `PlayCommand`, `PauseCommand`, `StepCommand`, `SeekCommand`, `SpeedCommand` | | `pswamp_models.player` |

**The data:** five stations, those of the sample recording, each with
`V_Magnitude` (kV), `V_Angle` (deg) and `f` (Hz), swinging slowly: frequency
over a day and over 37 s, voltage over an hour, angle over ten minutes.

**Settings** (a deployment sets `{SOURCE}_{SETTING}`, `HISTORY_SPAN` for a
source named `history`; a script passes keywords):

| Setting | Default | |
|---|---|---|
| `start` | `2025-10-01T00:00:00Z` | The first instant, ISO 8601 |
| `span` | a year | Seconds of data from `start` |
| `rate` | `20` | Frames per second; must divide 1 000 000, so every timestamp is a whole microsecond |
| `outages` | three, below | Comma-separated `<iso start>/<iso end>` ranges, half-open, with no frames |
| `gap` | `1` | Seconds without frames that the player crosses at once and reports (every playable source has it) |

The default outages: a 2.5 s dropout ten seconds in
(`2025-10-01T00:00:10.025Z` to `00:00:12.5Z`), 15 minutes from
`2025-11-03T12:00Z`, and three days from `2026-01-10T00:00Z`.

**Why it is fast:** a read from any instant computes the first frame index
there, and an outage is a jump in the index, so `read(t)` costs the same a
year in as at the start, and the source holds no frames in memory.

## From a script

```python
from pswamp_modules.synthetic_history import SyntheticHistory

source = SyntheticHistory()
source.coverage()                    # [first frame, last + one interval)
next(source.read(start))             # the first frame at or after start
list(source.read(start, end))        # a half-open range [start, end)
```

Don't `list(source.read())` the default: that is 630 million frames.

## Behind the remote data stub

    REMOTE_DATA_STUB_SOURCE=history:synthetic-history PYTHONPATH=modules/remote-history/examples \
        uv run python -m remote_data_stub

`HISTORY_*` variables then configure it.

## Examples

`examples/read_synthetic_history.py` reads slices around two outages:

    uv run python modules/synthetic-history/examples/read_synthetic_history.py

## Tests

`uv run pswamp test module synthetic-history` (also part of `uv run pswamp test server`).
The source passes `pswamp_core.testing.SourceConformance` over a three-second
span with one outage.
