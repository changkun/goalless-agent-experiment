"""
Collatz trajectory hunter.

Scans 1..N for the longest 3n+1 trajectories ("total stopping times"),
then renders the top few as height-normalized ASCII sparklines so the
shape of each trajectory is visible at a glance.
"""

import sys

BLOCKS = " ▁▂▃▄▅▆▇█"


def trajectory(n: int) -> list[int]:
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq


def stopping_times(limit: int) -> dict[int, int]:
    """Memoized stopping times for 1..limit. O(limit) amortized."""
    cache: dict[int, int] = {1: 0}
    for start in range(2, limit + 1):
        n, steps = start, 0
        path: list[int] = []
        while n not in cache:
            path.append(n)
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            steps += 1
        base = cache[n]
        for i, v in enumerate(reversed(path), 1):
            cache[v] = base + i
    return cache


def sparkline(seq: list[int], width: int) -> str:
    """Sample seq down to `width` points, render with Unicode blocks."""
    if len(seq) <= width:
        sample = seq
    else:
        step = (len(seq) - 1) / (width - 1)
        sample = [seq[round(i * step)] for i in range(width)]
    peak = max(sample)
    if peak == 0:
        return BLOCKS[0] * len(sample)
    return "".join(BLOCKS[min(len(BLOCKS) - 1, round(v / peak * (len(BLOCKS) - 1)))] for v in sample)


def main(limit: int = 100_000, top: int = 12, width: int = 60) -> None:
    print(f"scanning 1..{limit:,} for longest collatz trajectories\n")
    cache = stopping_times(limit)

    leaders = sorted(((steps, n) for n, steps in cache.items() if 2 <= n <= limit),
                     key=lambda x: (-x[0], x[1]))[:top]

    longest = max(s for s, _ in leaders)
    print(f"  {'n':>10}  {'steps':>6}  {'peak':>14}  trajectory")
    print(f"  {'-'*10}  {'-'*6}  {'-'*14}  {'-'*width}")
    for steps, n in leaders:
        seq = trajectory(n)
        bar = sparkline(seq, width)
        mark = " ←" if steps == longest else ""
        print(f"  {n:>10,}  {steps:>6}  {max(seq):>14,}  {bar}{mark}")

    print(f"\nlongest under {limit:,}: n={leaders[0][1]:,} took {leaders[0][0]} steps")
    print(f"highest peak seen: {max(max(trajectory(n)) for _, n in leaders):,}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    main(limit)
