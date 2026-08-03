"""Allow ``python -m markovgen`` to invoke the CLI."""

from .cli import main

raise SystemExit(main())
