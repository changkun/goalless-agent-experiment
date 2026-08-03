"""passgen: generate strong passphrases and passwords with entropy math."""

from .core import (
    main,
    DEFAULT_WORDLIST,
    entropy,
    generate_password,
    generate_passphrase,
)

__all__ = [
    "main",
    "DEFAULT_WORDLIST",
    "entropy",
    "generate_password",
    "generate_passphrase",
]
__version__ = "0.1.0"
