"""Allow ``python -m game2048`` to launch the game."""
from .cli import play

if __name__ == "__main__":
    play()
