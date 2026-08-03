"""Core timer logic for the Pomodoro CLI.

The timer is a pure state machine that counts remaining seconds downward. It
never blocks or sleeps by itself; callers handle the pacing (for example, a
CLI tick loop). Keeping it dependency-free and non-blocking makes the logic
easy to test and reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SessionType(str, Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass(frozen=True)
class Session:
    type: SessionType
    duration_seconds: int
    label: str


DEFAULT_FOCUS_MINUTES = 25
DEFAULT_SHORT_BREAK_MINUTES = 5
DEFAULT_LONG_BREAK_MINUTES = 15
DEFAULT_SESSIONS_PER_CYCLE = 4


class Timer:
    """A countdown that alternates between focus and break sessions."""

    def __init__(
        self,
        focus_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_per_cycle: int = 4,
    ) -> None:
        for name, minutes in (
            ("focus", focus_minutes),
            ("short_break", short_break_minutes),
            ("long_break", long_break_minutes),
        ):
            if minutes < 1:
                raise ValueError(f"{name} duration must be at least 1 minute")
        if sessions_per_cycle < 1:
            raise ValueError("sessions_per_cycle must be at least 1")

        self.focus_seconds = focus_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.sessions_per_cycle = sessions_per_cycle

        self.focus_count = 0
        self.completed_sessions = 0
        self.session_type = SessionType.FOCUS
        self._remaining = self.focus_seconds

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def elapsed(self) -> int:
        return self.duration_for(self.session_type) - self._remaining

    def duration_for(self, session_type: SessionType | None = None) -> int:
        session_type = session_type or self.session_type
        if session_type is SessionType.FOCUS:
            return self.focus_seconds
        if session_type is SessionType.SHORT_BREAK:
            return self.short_break_seconds
        return self.long_break_seconds

    def _label_for(self, session_type: SessionType) -> str:
        if session_type is SessionType.FOCUS:
            return "Focus"
        if session_type is SessionType.SHORT_BREAK:
            return "Short break"
        return "Long break"

    def tick(self, seconds: int = 1) -> Session | None:
        """Advance by ``seconds``.

        When a session ends, the timer switches to the next one and returns
        the just-completed session so the caller can announce it. Returns
        ``None`` when the current session is still running.
        """
        if seconds < 1:
            raise ValueError("seconds must be at least 1")

        completed: Session | None = None
        self._remaining -= seconds
        while self._remaining <= 0:
            completed = self._complete_current(self._remaining)
        return completed

    def _complete_current(self, overflow: int) -> Session:
        finished_type = self.session_type
        finished = Session(
            type=finished_type,
            duration_seconds=self.duration_for(finished_type),
            label=self._label_for(finished_type),
        )

        if finished_type is SessionType.FOCUS:
            self.focus_count += 1
            self.completed_sessions += 1
            if self.focus_count % self.sessions_per_cycle == 0:
                self.session_type = SessionType.LONG_BREAK
            else:
                self.session_type = SessionType.SHORT_BREAK
        else:
            self.session_type = SessionType.FOCUS

        self._remaining = self.duration_for() + overflow
        return finished


def format_time(seconds: int) -> str:
    """Format seconds as ``MM:SS``, suitable for a terminal clock."""
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def format_time(seconds: int) -> str:
    """Format seconds as ``MM:SS`` (or ``H:MM:SS`` beyond an hour)."""
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
