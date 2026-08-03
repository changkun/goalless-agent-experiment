"""Passgen: a dependency-free password and token generation toolkit."""

__version__ = "0.1.0"

from .core import (
    PasswordConfig,
    generate_password,
    generate_passphrase,
    entropy,
)

__all__ = [
    "PasswordConfig",
    "generate_password",
    "generate_passphrase",
    "entropy",
    "__version__",
]
