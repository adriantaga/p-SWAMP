# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the p-SWAMP Project.

"""The player's commands: what a page (or a module) asks of a run's replay.

Each class is its own address (see ``pswamp_models.common.Command``); the
player is the one receiver of every ``PlayerCommand``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ..common.command import Command
from ..common.utc import ensure_utc

__all__ = [
    "PauseCommand",
    "PlayCommand",
    "PlayerCommand",
    "SeekCommand",
    "SpeedCommand",
    "StepCommand",
    "SwitchSourceCommand",
]


class PlayerCommand(Command):
    """Base of the commands the player handles."""


class PlayCommand(PlayerCommand):
    """Start or resume the replay."""


class PauseCommand(PlayerCommand):
    """Pause the replay where it is."""


class StepCommand(PlayerCommand):
    """Play ``n`` frames at once, unpaced; a negative ``n`` steps back."""

    n: int = Field(default=1, description="Frames to step; negative steps back.")


class SeekCommand(PlayerCommand):
    """Move the replay to the instant ``at``: the first frame at or after it.

    With ``until`` it plays only ``[at, until)`` and ends paused there, instead
    of running on or looping: a chunk. An instant without a zone is UTC.
    """

    version: Literal["v2"] = "v2"
    at: datetime = Field(description="The instant to go to, UTC.")
    until: datetime | None = Field(default=None, description="Stop here instead of running on: exclusive, UTC.")
    play: bool = Field(default=False, description="Also start playing, if paused.")

    @field_validator("at", "until")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else ensure_utc(value)

    @model_validator(mode="after")
    def _until_after_at(self) -> SeekCommand:
        if self.until is not None and self.until <= self.at:
            raise ValueError("until must be after at")
        return self


class SpeedCommand(PlayerCommand):
    """Change the replay speed."""

    speed: float = Field(gt=0, description="Speed multiplier; 1 is real time.")


class SwitchSourceCommand(PlayerCommand):
    """Read another of the pipeline's sources.

    A recording lands paused at its start; a live source is followed from now.
    """

    source: str = Field(description="The source's name, as the pipeline declares it.")
