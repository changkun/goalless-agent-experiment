"""Pure timer-state logic for the focus timer.

This module has no I/O or time dependence, which keeps it easy to unit test.
"""

from __future__ import annotations

from dataclasses import dataclass

PHASE_FOCUS = "focus"
PHASE_BREAK = "break"


@dataclass(frozen=True)
class Cycle:
    """How long a focus session and its following break last, in seconds."""

    focus_seconds: int
    break_seconds: int

    @classmethod
    def from_minutes(cls, focus: float, break_: float) -> "Cycle":
        return cls(round(focus * 60), round(break_ * 60))


@dataclass(frozen=True)
class Frame:
    """The state of the timer at a given elapsed time (in seconds)."""

    phase: str
    remaining_seconds: int
    cycle_seconds: int
    phase_seconds: int
    completed_focus_sessions: int
    percent: float  # 0.0 -> 1.0 completed of the current phase

    @property
    def is_focus(self) -> bool:
        return self.phase == PHASE_FOCUS

    @property
    def label(self) -> str:
        return "FOCUS" if self.is_focus else "BREAK"


def frame_at(elapsed_seconds: int, cycle: Cycle) -> Frame:
    """Return the timer frame for a given number of elapsed seconds."""
    total = cycle.focus_seconds + cycle.break_seconds
    if total <= 0:
        raise ValueError("cycle must have a positive total duration")

    elapsed = max(0, elapsed_seconds)

    full_cycles, offset = divmod(elapsed, total)
    if offset < cycle.focus_seconds:
        phase = PHASE_FOCUS
        phase_elapsed = offset
        phase_duration = cycle.focus_seconds
    else:
        phase = PHASE_BREAK
        phase_elapsed = offset - cycle.focus_seconds
        phase_duration = cycle.break_seconds

    completed_sessions = full_cycles + (1 if offset >= cycle.focus_seconds else 0)

    remaining = max(0, phase_duration - phase_elapsed)
    percent = (
        1.0 if phase_duration == 0 else min(1.0, phase_elapsed / phase_duration)
    )

    return Frame(
        phase=phase,
        remaining_seconds=remaining,
        cycle_seconds=total,
        phase_seconds=phase_duration,
        completed_focus_sessions=completed_sessions,
        percent=percent,
    )
