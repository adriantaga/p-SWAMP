# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""``SummarizeRangeCommand``: ask the range summary module about part of a recording."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from ..common.command import Command
from ..common.utc import ensure_utc

__all__ = ["SummarizeRangeCommand"]


class SummarizeRangeCommand(Command):
    """Summarize ``[start, end)`` of a recording. An instant without a zone is UTC."""

    version: Literal["v2"] = "v2"
    source: str = Field(description="The recording: a history source of the pipeline.")
    start: datetime = Field(description="Inclusive start, UTC.")
    end: datetime = Field(description="Exclusive end, UTC.")

    @field_validator("start", "end")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
