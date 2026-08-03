"""gitpulse — a quick health check for a git repository.

Reads commit history through git plumbing (no external dependencies) and
reports activity pace, author distribution, bus-factor, and churn hotspots.
"""

__version__ = "0.1.0"

from .analyzer import analyze

__all__ = ["analyze", "__version__"]
