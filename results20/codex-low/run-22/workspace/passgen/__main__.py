"""Support running as ``python -m passgen``."""

from .cli import main
import sys

sys.exit(main())
