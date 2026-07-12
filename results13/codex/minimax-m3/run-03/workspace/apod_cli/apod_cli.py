"""Console-script entry point so `python -m apod_cli` or the installed
``apod`` command both work."""
from apod_cli.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
