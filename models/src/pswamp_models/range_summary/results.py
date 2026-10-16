# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""``RangeSummaryResult`` (topic ``range.summary.result``): the answer to a ``SummarizeRangeCommand``."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from ..common.results import ResultEnvelope

__all__ = ["RangeSummary", "RangeSummaryResult"]


class RangeSummary(BaseModel):
    source: str
    start: datetime = Field(description="The range summarized: inclusive start, UTC.")
    end: datetime = Field(description="Exclusive end, UTC.")
    frames: int = Field(description="Frames in the range.")
    min_frequency_hz: float
    max_frequency_hz: float
    mean_frequency_hz: float


class RangeSummaryResult(ResultEnvelope[RangeSummary]):
    version: Literal["v2"] = "v2"
