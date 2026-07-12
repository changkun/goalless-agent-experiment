#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           🌌  COSMIC WEATHER REPORT  🌌                 ║
║     Your daily forecast from the edge of the galaxy      ║
╚══════════════════════════════════════════════════════════╝

A retro terminal app that generates randomized space weather
forecasts with ASCII art. Because the universe has moods too.
"""

import random
import time
import os
import sys
import math

# ─── ANSI helpers ───────────────────────────────────────────────

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"

PALETTE = {
    "nebula_pink":   rgb(255, 100, 150),
    "cosmic_blue":   rgb(80,  140, 255),
    "solar_gold":    rgb(255, 210, 80),
    "void_purple":   rgb(160, 80,  220),
    "star_white":    rgb(240, 240, 255),
    "asteroid_grey": rgb(140, 140, 160),
    "plasma_green":  rgb(80,  255, 140),
    "dark_red":      rgb(200, 50,  50),
}

# ─── Data banks ─────────────────────────────────────────────────

CELESTIAL_BODIES = [
    ("Andromeda Suburbs",   "nebula_pink"),
    ("Orion's Beltway",    "cosmic_blue"),
    ("The Crab Nebula",    "solar_gold"),
    ("Sagittarius A*",     "void_purple"),
    ("Europa's Oceans",    "cosmic_blue"),
    ("Titan's Methane Lakes", "solar_gold"),
    ("The Kuiper Belt",    "asteroid_grey"),
    ("Proxima Station",    "plasma_green"),
    ("Vega Downtown",      "star_white"),
    ("The Oort Cloud",     "asteroid_grey"),
    ("Ganymede Heights",   "cosmic_blue"),
    ("The Pillars of Creation", "nebula_pink"),
]

WEATHER_CONDITIONS = [
    ("Solar Flare Warning",        "☀️", "solar_gold"),
    ("Nebula Fog",                 "🌫️", "nebula_pink"),
    ("Meteor Shower",              "☄️", "asteroid_grey"),
    ("Quantum Precipitation",      "🌧️", "cosmic_blue"),
    ("Cosmic Ray Storm",           "⚡", "plasma_green"),
    ("Gravitational Ripple",       "🌊", "cosmic_blue"),
    ("Dark Matter Drizzle",        "🌑", "void_purple"),
    ("Aurora Borealis Extravaganza","🌈", "nebula_pink"),
    ("Spacetime Fold",             "📄", "void_purple"),
    ("Interstellar Dust Devils",   "🌪️", "asteroid_grey"),
    ("Plasma Rain",               "🔬", "plasma_green"),
    ("Photon Blizzard",           "❄️", "star_white"),
    ("Warp Field Distortion",     "🌀", "void_purple"),
    ("Binary Star Eclipse",       "🌓", "solar_gold"),
    ("Pulsar Signal Interference","📡", "cosmic_blue"),
]

TEMP_RANGES = [
    ("Absolute zero with wind chill", -273),
    ("Crisp and existential",         -180),
    ("Brisk — wear your space parka", -90),
    ("Mildly radioactive",            42),
    ("Room temp (if your room is Venus", 462),
    ("Surface-of-a-star toasty",      5500),
    ("Quark-gluon plasma hot",        2_000_000_000),
    ("Planck temperature absurd",     1_417_000_000_000_000_000_000_000_000),
]

UV_INDEX = [
    "Negligible (1)",
    "Moderate — SPF 50 recommended (4)",
    "High — wear a lead suit (7)",
    "Extreme — do not exist outdoors (11)",
    "Supernova-class — SPF 1,000,000 (42)",
    "Gamma-ray burst imminent — goodbye (∞)",
]

WIND = [
    "Calm — stardust gently settling",
    "Light breeze — solar wind at 400 km/s",
    "Gusty — rogue planet tailwind",
    "Hurricane — magnetar spin-kick",
    "Tornadic — black hole accretion disk jet",
    "Timeless — light-speed headwind",
]

VISIBILITY = [
    "Clear — can see to the edge of the observable universe",
    "Good — CMB glow on the horizon",
    "Fair — some nebula haze",
    "Poor — asteroid field obstruction",
    "Zero — you are inside a gas giant",
]

SPACE_SEA = [
    "Calm — cosmic pond conditions",
    "Choppy — dark matter currents",
    "Rough — tidal forces from a nearby pulsar",
    "Tsunami advisory — gravity wave detected",
    "Sailing not recommended — event horizon ahead",
]

ASCII_ARTS = {
    "nebula": r"""
      .  *  .   *    .  .   *
   .    ___   .    .    *   .
 *   .'   '.   *   .    .
   .'  .-°-.  '.     *    .
  .  .'  |  '.  .   .   .
    .  '--+--'  .     .
  *    '. | .'  *   .    *
   *    '.|.'      .    .
      *   |   .    *   .
   .   *  |  .   .    *   .
""",
    "planet": r"""
            .  *  .
        *       .      *
     .    ___            .
        /   \    *   .
   *   |  O  |      .
       |     |   *     .
   .    \___/    .   *
        .    *       .
     *      .    *     .
        .          .
""",
    "blackhole": r"""
         .   *    .
    .        .        *
       ___        .
     /     \    *    .
    |  .-.  |---.     *
    | ( o ) |   |  .
     \  '-' /---'    *
   *  '---'       .
    .        *       .
        .   *    .
""",
    "rocket": r"""
          /\
         /  \
        / ** \
       /______\
      /        \
     /  ENGAGE  \
    /____________\
    |  |    |  |  *
    |  |    |  |
    |  |    |  |   .
    |__|____|__|
       /    \
      / FIRE  \
     /__________\
        |    |
       /|    |\
""",
    "alien": "\n       .-''''-.\n      /  o  o  \\\n     |    __    |\n   .-'\\  }{  /'-.\n  /  _  }{  _  \\     *\n |  / \\  }{  / \\  |   .\n |  \\_/  }{  \\_/  |\n  \\  _  }{  _  /\n   '-\\  }{  /-'\n      '----'\n",
}

ADVICE = [
    "Avoid making any major life decisions during a meteor shower.",
    "Today is favorable for first contact protocols.",
    "Your aura is especially luminous — charge your crystals in starlight.",
    "Do not taunt the gravity well.",
    "An old flame (literally, a star) is thinking of you from 4.2 light-years away.",
    "Trust your instincts — unless they involve opening airlocks.",
    "The stars say: deploy the solar sails.",
    "Romance is in the air — or that's just ionized nitrogen.",
    "Today's lucky element: Ununpentium (115).",
    "A wormhole to a better timeline opens at 3:47 PM.",
    "Beware of Ferengi bearing gifts.",
    "Your convergence of timelines suggests: take a nap.",
    "The cosmic background radiation aligns with your chakras today.",
    "Do NOT look directly at the supernova. (We cannot stress this enough.)",
    "Mercury is in retrograde — but when is it not?",
    "Fortune favors the bold and the well-shielded.",
    "Today's vibe: chaotic neutral with a chance of wonder.",
    "If someone offers you a ride in their TARDIS, say yes.",
]

FORECAST_NOTES = [
    "Interstellar highway conditions: Mostly clear with occasional asteroid.",
    "Space whale migration expected — reduce warp speed near nebulae.",
    "Cosmic microwave background is 2.725K today — right on schedule.",
    "Solar sail efficiency at maximum — perfect day for a lightsail cruise.",
    "The Great Attractor continues its pull — nothing new there.",
    "Dark energy expansion rate: still accelerating. Plan accordingly.",
    "Reminder: the Heat Death of the Universe is still on schedule for 10^100 years.",
    "Local galaxy group remains gravitationally bound — no cause for alarm.",
]

# ─── Drawing helpers ────────────────────────────────────────────

def draw_stars(width=60, count=15):
    """Return a line of random twinkling stars."""
    stars = []
    for _ in range(count):
        pos = random.randint(0, width - 1)
        char = random.choice(["·", "✦", "✧", "·", "·", "*", "∘", "°"])
        stars.append((pos, char))
    stars.sort()
    line = [" "] * width
    for pos, char in stars:
        line[pos] = char
    return PALETTE["star_white"] + "".join(line) + RESET


def draw_progress_bar(label, value, max_val, color_key, width=30):
    """Draw a labeled progress bar."""
    color = PALETTE[color_key]
    filled = int((value / max_val) * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = int((value / max_val) * 100)
    return f"  {color}{BOLD}{label:<18}{RESET} {color}[{bar}] {pct}%{RESET}"


def draw_divider(char="─", width=60, color_key="asteroid_grey"):
    color = PALETTE[color_key]
    return f"  {color}{char * width}{RESET}"


# ─── Report generation ─────────────────────────────────────────

def generate_report():
    """Generate a complete cosmic weather report."""

    # Pick today's celestial body
    location, loc_color = random.choice(CELESTIAL_BODIES)
    # Pick weather
    condition_name, condition_icon, cond_color = random.choice(WEATHER_CONDITIONS)
    # Temperature
    temp_label, temp_val = random.choice(TEMP_RANGES)
    # Other data
    uv = random.choice(UV_INDEX)
    wind = random.choice(WIND)
    vis = random.choice(VISIBILITY)
    sea = random.choice(SPACE_SEA)
    # ASCII art
    art_key = random.choice(list(ASCII_ARTS.keys()))
    art = ASCII_ARTS[art_key]
    # Advice
    advice = random.choice(ADVICE)
    # Forecast note
    note = random.choice(FORECAST_NOTES)

    # Random metrics for bars
    chaos = random.randint(5, 95)
    vibes = random.randint(10, 100)
    doom  = random.randint(0, 80)
    hope  = random.randint(20, 100)

    # Build the report
    lines = []
    W = 60

    # Header
    lines.append("")
    lines.append(draw_stars(W))
    lines.append("")
    loc_c = PALETTE[loc_color]
    lines.append(f"  {loc_c}{BOLD}⧖  LOCATION: {location.upper()}{RESET}")
    lines.append(f"  {PALETTE[cond_color]}{BOLD}{condition_icon}  CONDITIONS: {condition_name.upper()}{RESET}")
    lines.append(draw_divider("━", W, loc_color))
    lines.append("")

    # Temperature
    lines.append(f"  {PALETTE['solar_gold']}{BOLD}TEMPERATURE:{RESET} {temp_label}")
    if abs(temp_val) < 1_000_000:
        lines.append(f"  {PALETTE['solar_gold']}{temp_val:>10,} °C{RESET}")
    else:
        lines.append(f"  {PALETTE['solar_gold']}{temp_val:>10e} °C{RESET}")
    lines.append("")

    # Details
    lines.append(f"  {PALETTE['void_purple']}{BOLD}UV INDEX:{RESET}      {uv}")
    lines.append(f"  {PALETTE['cosmic_blue']}{BOLD}WIND:{RESET}          {wind}")
    lines.append(f"  {PALETTE['star_white']}{BOLD}VISIBILITY:{RESET}    {vis}")
    lines.append(f"  {PALETTE['plasma_green']}{BOLD}SPACE SEA:{RESET}     {sea}")
    lines.append("")

    # Bars
    lines.append(draw_divider("─", W, "asteroid_grey"))
    lines.append(f"  {PALETTE['nebula_pink']}{BOLD}COSMIC METRICS{RESET}")
    lines.append(draw_progress_bar("Chaos Index", chaos, 100, "void_purple"))
    lines.append(draw_progress_bar("Vibe Alignment", vibes, 100, "plasma_green"))
    lines.append(draw_progress_bar("Existential Doom", doom, 100, "dark_red"))
    lines.append(draw_progress_bar("Hope Quotient", hope, 100, "solar_gold"))
    lines.append(draw_divider("─", W, "asteroid_grey"))
    lines.append("")

    # ASCII art
    art_color = PALETTE[loc_color]
    colored_art = "\n".join(
        art_color + line + RESET for line in art.splitlines()
    )
    lines.append(colored_art)
    lines.append("")

    # Horoscope / advice
    lines.append(draw_divider("✦", W, "solar_gold"))
    lines.append(f"  {PALETTE['nebula_pink']}{BOLD}🔮 COSMIC ADVICE:{RESET}")
    lines.append(f"  {ITALIC}\"{advice}\"{RESET}")
    lines.append("")

    # Forecast note
    lines.append(f"  {PALETTE['asteroid_grey']}{DIM}📋 FORECASTER'S NOTE: {note}{RESET}")
    lines.append(draw_divider("✦", W, "solar_gold"))

    # Footer
    lines.append("")
    lines.append(draw_stars(W))
    lines.append(
        f"  {DIM}{PALETTE['asteroid_grey']}"
        f"Report generated at stardate {random.randint(40000,99999)}.{random.randint(1,9):d}"
        f"{RESET}"
    )
    lines.append(f"  {DIM}{PALETTE['asteroid_grey']} cosmos-weather://report/v{random.randint(1,9)}.{random.randint(0,20)}.{random.randint(0,99)}{RESET}")
    lines.append(draw_stars(W))
    lines.append("")

    return "\n".join(lines)


# ─── Animation ──────────────────────────────────────────────────

def loading_animation(duration=2.5):
    """Show a spinning loading animation."""
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    messages = [
        "Scanning the cosmic microwave background...",
        "Consulting the pulsar network...",
        "Calibrating the vibe-o-meter...",
        "Aligning with the galactic plane...",
        "Decoding dark matter signals...",
        "Synchronizing with spacetime...",
    ]
    msg = random.choice(messages)

    frames = int(duration * 10)
    for i in range(frames):
        frame = spinner[i % len(spinner)]
        sys.stdout.write(f"\r  {PALETTE['cosmic_blue']}{frame} {msg}{RESET}   ")
        sys.stdout.flush()
        time.sleep(0.1)

    sys.stdout.write(f"\r  {' ' * 60}\r")
    sys.stdout.flush()


# ─── Main ──────────────────────────────────────────────────────

def main():
    # Check terminal color support
    if not sys.stdout.isatty():
        # Strip colors if not a terminal
        for key in PALETTE:
            PALETTE[key] = ""

    print()
    print(f"  {PALETTE['void_purple']}{BOLD}{'═' * 60}{RESET}")
    print(f"  {PALETTE['void_purple']}{BOLD}║{RESET}  {PALETTE['star_white']}{BOLD}🌌  COSMIC WEATHER REPORT  🌌{RESET}  {PALETTE['void_purple']}{BOLD}║{RESET}")
    print(f"  {PALETTE['void_purple']}{BOLD}║{RESET}  {DIM}from the edge of the galaxy{RESET}    {PALETTE['void_purple']}{BOLD}║{RESET}")
    print(f"  {PALETTE['void_purple']}{BOLD}{'═' * 60}{RESET}")
    print()

    # Loading animation
    loading_animation(2.0)

    # Generate and print report
    report = generate_report()
    print(report)

    # Interactive prompt
    print(f"  {PALETTE['cosmic_blue']}{BOLD}Press ENTER for another report, or q to quit.{RESET}")

    try:
        while True:
            key = input()
            if key.lower() in ("q", "quit", "exit"):
                break
            loading_animation(1.5)
            report = generate_report()
            print(report)
            print(f"  {PALETTE['cosmic_blue']}{BOLD}Press ENTER for another report, or q to quit.{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass

    print()
    print(f"  {PALETTE['void_purple']}{ITALIC}May your orbits be stable and your skies be clear. 🌌{RESET}")
    print()


if __name__ == "__main__":
    main()
