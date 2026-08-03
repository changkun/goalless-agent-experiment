"""Project-specific exceptions."""


class GitPulseError(Exception):
    """Base class for all gitpulse errors."""


class NotAGitRepo(GitPulseError):
    """Raised when a path is not a git working tree."""

    def __init__(self, path: str) -> None:
        super().__init__(f"{path!r} is not inside a git working tree")
        self.path = path
