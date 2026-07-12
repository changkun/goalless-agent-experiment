#!/usr/bin/env python3
"""
Cellular Automaton Art Generator
Generates beautiful patterns using 1D elementary cellular automata
with colorful terminal output.
"""

import os
import random
import sys
import time

# ANSI color codes for terminal output
COLORS = [
    "\033[38;5;196m",  # Red
    "\033[38;5;202m",  # Orange
    "\033[38;5;226m",  # Yellow
    "\033[38;5;46m",  # Green
    "\033[38;5;51m",  # Cyan
    "\033[38;5;45m",  # Blue
    "\033[38;5;129m", # Purple
    "\033[38;5;201m", # Magenta
]
RESET = "\033[0m"
BLOCK = "█"
BLANK = " "
CLEAR = "\033[2J\033[H"

# Some of the most visually interesting Wolfram rules
INTERESTING_RULES = [30, 90, 110, 150, 182, 60, 45, 73, 105, 126, 150, 225]

def get_rule_number():
    """Pick a rule, prioritizing the visually stunning ones."""
    if random.random() < 0.7:
        return random.choice(INTERESTING_RULES)
    return random.randint(0, 255)

def apply_rule(rule_num, left, center, right):
    """Apply an elementary CA rule to a cell given its 3-neighborhood."""
    index = (left << 2) | (center << 1) | right
    return (rule_num >> index) & 1

def next_generation(row, rule_num):
    """Compute the next generation of a 1D CA."""
    width = len(row)
    new = []
    for i in range(width):
        left = row[(i - 1) % width]
        center = row[i]
        right = row[(i + 1) % width]
        new.append(apply_rule(rule_num, left, center, right))
    return new

def render_row(row, gen, color_offset=0):
    """Render a row with cycling colors based on generation."""
    result = []
    for cell in row:
        if cell:
            color_idx = (gen + color_offset) % len(COLORS)
            result.append(f"{COLORS[color_idx]}{BLOCK}{RESET}")
        else:
            result.append(f"{BLANK}")
    return "".join(result)

def get_terminal_width():
    """Get terminal width, defaulting to 80."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def get_terminal_height():
    """Get terminal height, defaulting to 24."""
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24

def make_initial_state(width, mode="single"):
    """Create the initial state for the CA."""
    row = [0] * width
    if mode == "single":
        row[width // 2] = 1
    elif mode == "random":
        row = [random.randint(0, 1) for _ in range(width)]
    elif mode == "sparse":
        for i in range(width):
            if random.random() < 0.05:
                row[i] = 1
    return row

def run_automaton():
    """Run the cellular automaton display."""
    width = get_terminal_width() - 2
    height = get_terminal_height() - 4

    if width < 20 or height < 10:
        width, height = 78, 20

    rule_num = get_rule_number()
    init_mode = random.choice(["single", "random", "sparse"])

    # Print header
    print(CLEAR)
    print(f"\033[1m\033[38;5;255m  ✦ Cellular Automaton Art ✦\033[0m")
    print(f"\033[38;5;246m  Rule {rule_num} | Init: {init_mode} | Width: {width}\033[0m")
    print()

    state = make_initial_state(width, init_mode)

    try:
        for gen in range(height):
            line = render_row(state, gen)
            print(f"  {line}")
            state = next_generation(state, rule_num)
            # Slow down slightly for visual effect
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\n{RESET}\033[38;5;246m  Interrupted. Goodbye! ✦\033[0m")
        return

    print()
    print(f"\033[38;5;246m  Rule {rule_num} complete. Press Ctrl+C to exit or wait for next...\033[0m")

    # Run additional patterns if not interrupted
    time.sleep(1.5)
    for _ in range(20):
        rule_num = get_rule_number()
        init_mode = random.choice(["single", "random", "sparse"])
        print(CLEAR)
        print(f"\033[1m\033[38;5;255m  ✦ Cellular Automaton Art ✦\033[0m")
        print(f"\033[38;5;246m  Rule {rule_num} | Init: {init_mode} | Width: {width}\033[0m")
        print()

        state = make_initial_state(width, init_mode)

        try:
            for gen in range(height):
                line = render_row(state, gen)
                print(f"  {line}")
                state = next_generation(state, rule_num)
                time.sleep(0.02)
        except KeyboardInterrupt:
            print(f"\n{RESET}\033[38;5;246m  Goodbye! ✦\033[0m")
            return

        print()
        print(f"\033[38;5;246m  Rule {rule_num} complete. ✦\033[0m")
        time.sleep(1.0)

if __name__ == "__main__":
    run_automaton()
