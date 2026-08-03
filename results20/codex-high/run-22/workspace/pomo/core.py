"""Core pomodoro timer engine.

The engine is deliberately time-independent so it can be driven by an
external clock (e.g. a ``time.monotonic``-backed callable) and therefore
tested deterministically.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto


class Phase(Enum):
    """The distinct phases of a pomodoro cycle."""

    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()


@dataclass
class Session:
    """A record of one completed work pomodoro."""

    task: str
    duration_s: int
    completed_at: float


@dataclass
class PomodoroTimer:
    """A stateful, clock-injectable pomodoro timer.

    Attributes:
        work_s: length of a work phase in seconds.
        short_break_s: length of a short break in seconds.
        long_break_s: length of a long break in seconds.
        long_break_every: complete ``N`` work pomodoros before a long break.
        clock: callable returning the current time in seconds (float).
    """

    work_s: int = 25 * 60
    short_break_s: int = 5 * 60
    long_break_s: int = 15 * 60
    long_break_every: int = 4
    clock: callable = field(default=time.monotonic)

    def __post_init__(self) -> None:
        self.phase: Phase = Phase.WORK
        self._started: float = self.clock()
        self.remaining_s: int = self.work_s
        self.completed_work: int = 0
        self.sessions: list[Session] = []
        self._task: str = ""

    @property
    def phase_name(self) -> str:
        return self.phase.name.replace("_", " ").title()

    @property
    def total_s(self) -> int:
        """Total length (seconds) of the current phase."""
        if self.phase is Phase.WORK:
            return self.work_s
        if self.phase is Phase.SHORT_BREAK:
            return self.short_break_s
        return self.long_break_s

    def tick(self, now: float | None = None) -> None:
        """Advance the timer by recomputing remaining time from the clock."""
        now = self.clock() if now is None else now
        elapsed = int(now - self._started)
        self.remaining_s = max(0, self.total_s - elapsed)

    def _switch(self, next_phase: Phase) -> None:
        self.phase = next_phase
        self._started = self.clock()
        self.remaining_s = self.total_s

    def advance(self, now: float | None = None) -> Phase:
        """Finish the current phase, record results, and start the next.

        Returns the newly started phase. This is the driving force behind
        the whole cycle:
        * WORK -> short break (or long break every ``N`` sessions)
        * break -> WORK
        """
        if self.phase is Phase.WORK:
            self.completed_work += 1
            self.sessions.append(
                Session(
                    task=self._task,
                    duration_s=self.total_s,
                    completed_at=self.clock() if now is None else now,
                )
            )
            if self.completed_work % self.long_break_every == 0:
                self._switch(Phase.LONG_BREAK)
            else:
                self._switch(Phase.SHORT_BREAK)
        else:
            self._switch(Phase.WORK)
        self.tick(now)
        return self.phase

    def skip(self) -> Phase:
        """Skip the current break phase and return to work.

        Skipping work is not allowed; use :meth:`advance` instead.
        """
        if self.phase is Phase.WORK:
            raise ValueError("cannot skip a work phase")
        self._switch(Phase.WORK)
        return self.phase

    def set_task(self, task: str) -> None:
        """Record the task label for the current (or next) work phase."""
        self._task = task
