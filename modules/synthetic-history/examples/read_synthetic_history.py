# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""Read the Synthetic history source from a plain script: no server, no transport, no event loop.

It holds a year, so the script reads slices: one at the 15 min outage, one
across the short dropout ten seconds in.

    uv run python modules/synthetic-history/examples/read_synthetic_history.py
"""

from datetime import datetime, timedelta, timezone
from itertools import islice

from pswamp_modules.synthetic_history import SyntheticHistory


def main() -> None:
    source = SyntheticHistory()
    coverage = source.coverage()
    print(f"holds [{coverage.start}, {coverage.end}), {(coverage.end - coverage.start).days} days")
    before = datetime(2025, 11, 3, 11, 59, 59, 900_000, tzinfo=timezone.utc)
    frames = list(islice(source.read(before), 4))
    print("around the 15 min outage:", ", ".join(f"{f.timestamp:%H:%M:%S.%f}" for f in frames))
    start = coverage.start + timedelta(seconds=9)
    chunk = list(source.read(start, start + timedelta(seconds=5)))
    print(f"[9 s, 14 s) holds {len(chunk)} frames, not 100: the dropout is 2.5 s")


if __name__ == "__main__":
    main()
