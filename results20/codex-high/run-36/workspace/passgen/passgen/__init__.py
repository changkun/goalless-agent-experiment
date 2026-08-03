"""passgen: a small, dependency-free password generator and analyzer."""

from .core import StrengthError, analyze_strength, generate_password

__all__ = ["StrengthError", "analyze_strength", "generate_password"]
__version__ = "0.1.0"
