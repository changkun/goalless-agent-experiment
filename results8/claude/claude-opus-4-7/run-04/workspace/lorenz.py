"""Trace the Lorenz attractor into an ASCII canvas."""

W, H = 100, 36
SIGMA, RHO, BETA = 10.0, 28.0, 8 / 3
DT, STEPS = 0.005, 60_000
SHADES = " .:-=+*#%@"


def step(x, y, z):
    return (
        x + DT * SIGMA * (y - x),
        y + DT * (x * (RHO - z) - y),
        z + DT * (x * y - BETA * z),
    )


def main():
    counts = [[0] * W for _ in range(H)]
    x, y, z = 0.1, 0.0, 0.0
    xs, zs = [], []
    for _ in range(STEPS):
        x, y, z = step(x, y, z)
        xs.append(x)
        zs.append(z)

    xmin, xmax = min(xs), max(xs)
    zmin, zmax = min(zs), max(zs)
    pad = 0.04
    xr = (xmax - xmin) * (1 + 2 * pad)
    zr = (zmax - zmin) * (1 + 2 * pad)
    x0 = xmin - (xmax - xmin) * pad
    z0 = zmin - (zmax - zmin) * pad

    peak = 0
    for x, z in zip(xs, zs):
        col = int((x - x0) / xr * (W - 1))
        row = int((1 - (z - z0) / zr) * (H - 1))
        counts[row][col] += 1
        if counts[row][col] > peak:
            peak = counts[row][col]

    out = []
    for row in counts:
        line = []
        for c in row:
            if c == 0:
                line.append(" ")
            else:
                idx = min(len(SHADES) - 1, 1 + int((c / peak) ** 0.4 * (len(SHADES) - 2)))
                line.append(SHADES[idx])
        out.append("".join(line).rstrip())
    print("\n".join(out))


if __name__ == "__main__":
    main()
