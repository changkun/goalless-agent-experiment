"""Reverse-mode autodiff from scratch, used to untangle two spirals.

No dependencies. No numpy. Every gradient in here is computed by the ~60 lines
of Value below, and the payoff is printed as terminal art.

    python3 spiral.py
"""

import math
import random
import sys

# ---------------------------------------------------------------- autodiff ---


class Value:
    """A scalar that remembers how it was made, so it can be differentiated."""

    __slots__ = ("data", "grad", "_backward", "_prev")

    def __init__(self, data, _children=(), _backward=None):
        self.data = data
        self.grad = 0.0
        self._prev = _children
        self._backward = _backward or (lambda: None)

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __pow__(self, k):
        out = Value(self.data**k, (self,))

        def _backward():
            self.grad += k * self.data ** (k - 1) * out.grad

        out._backward = _backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,))

        def _backward():
            self.grad += (1.0 - t * t) * out.grad

        out._backward = _backward
        return out

    def softplus(self):
        """log(1 + e^x), computed in the numerically stable direction."""
        x = self.data
        s = x + math.log1p(math.exp(-x)) if x > 0 else math.log1p(math.exp(x))
        out = Value(s, (self,))

        def _backward():
            self.grad += 1.0 / (1.0 + math.exp(-x)) * out.grad

        out._backward = _backward
        return out

    def backward(self):
        """Seed d(self)/d(self) = 1 and push it back through the whole graph."""
        order, seen, stack = [], set(), [(self, False)]
        while stack:  # iterative post-order: recursion would blow the stack
            node, expanded = stack.pop()
            if expanded:
                order.append(node)
                continue
            if id(node) in seen:
                continue
            seen.add(id(node))
            stack.append((node, True))
            for child in node._prev:
                stack.append((child, False))

        self.grad = 1.0
        for node in reversed(order):
            node._backward()

    def __neg__(self):
        return self * -1.0

    def __sub__(self, other):
        return self + (-other)

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def __repr__(self):
        return f"Value({self.data:.4f}, grad={self.grad:.4f})"


# ------------------------------------------------------------------ network ---


class MLP:
    """Fully connected tanh network. Weights live as flat lists of Values."""

    def __init__(self, sizes, rng):
        self.layers = []
        for nin, nout in zip(sizes, sizes[1:]):
            gain = math.sqrt(1.0 / nin)  # keep activations off the tanh tails
            self.layers.append(
                (
                    [[Value(rng.uniform(-gain, gain)) for _ in range(nin)] for _ in range(nout)],
                    [Value(0.0) for _ in range(nout)],
                )
            )

    def __call__(self, x):
        act = [xi if isinstance(xi, Value) else Value(xi) for xi in x]
        for i, (weights, biases) in enumerate(self.layers):
            out = []
            for row, b in zip(weights, biases):
                total = b
                for w, a in zip(row, act):
                    total = total + w * a
                out.append(total)
            act = out if i == len(self.layers) - 1 else [v.tanh() for v in out]
        return act[0]

    def parameters(self):
        return [p for w, b in self.layers for row in w for p in row] + [
            p for w, b in self.layers for p in b
        ]


# --------------------------------------------------------------------- data ---


def two_spirals(n_per_class, turns, noise, rng):
    """Two interleaved Archimedean spirals, offset by half a revolution."""
    points = []
    for label, phase in ((+1, 0.0), (-1, math.pi)):
        for i in range(n_per_class):
            t = (i + 1) / n_per_class
            angle = phase + t * turns * 2 * math.pi
            radius = 0.15 + 0.85 * t
            x = radius * math.cos(angle) + rng.gauss(0, noise)
            y = radius * math.sin(angle) + rng.gauss(0, noise)
            points.append(((x, y), label))
    rng.shuffle(points)
    return points


# ---------------------------------------------------------------- rendering ---


RESET = "\x1b[0m"
COOL = (33, 39, 45, 51)  # blues  -> class -1
WARM = (208, 214, 220, 226)  # ambers -> class +1
SHADES = "░▒▓█"


def paint(score, scale):
    """Confidence -> (sgr, glyph). Near the boundary, fade to a faint dot.

    A well-trained net is saturated almost everywhere (|score| ~ 20), so a fixed
    normalisation would paint every cell solid and hide the shape. Scale comes
    from the score distribution itself, which keeps the mid-tones alive.
    """
    conf = min(1.0, abs(score) / scale)
    if conf < 0.10:
        return "38;5;244", "·"
    tier = min(3, int(conf * 4))
    return f"38;5;{(WARM if score > 0 else COOL)[tier]}", SHADES[tier]


def render(net, data, width=78, height=34, extent=1.45):
    scores = [[0.0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            # cells are ~2:1, so x steps twice as fast per character
            x = -extent + 2 * extent * (col + 0.5) / width
            y = extent - 2 * extent * (row + 0.5) / height
            scores[row][col] = net((x, y)).data

    flat = sorted(abs(s) for r in scores for s in r)
    scale = flat[int(0.75 * len(flat))] or 1.0  # 75th percentile saturates
    cells = [[paint(s, scale) for s in row] for row in scores]

    for (x, y), label in data:
        col = int((x + extent) / (2 * extent) * width)
        row = int((extent - y) / (2 * extent) * height)
        if 0 <= row < height and 0 <= col < width:
            cells[row][col] = ("1;38;5;214", "O") if label > 0 else ("1;38;5;39", "X")

    border = "\x1b[38;5;240m"
    print(f"{border}┌{'─' * width}┐{RESET}")
    for row in cells:
        out, active = [], None
        for sgr, glyph in row:  # only emit an escape when the style changes
            if sgr != active:
                out.append(f"\x1b[{sgr}m")
                active = sgr
            out.append(glyph)
        print(f"{border}│{RESET}{''.join(out)}{RESET}{border}│{RESET}")
    print(f"{border}└{'─' * width}┘{RESET}")


def sparkline(values, height_chars="▁▂▃▄▅▆▇█", width=60):
    step = max(1, len(values) // width)
    sampled = values[::step][:width]
    lo, hi = min(sampled), max(sampled)
    span = hi - lo or 1.0
    return "".join(height_chars[min(7, int((v - lo) / span * 8))] for v in sampled)


# ------------------------------------------------------------------ training ---


class Adam:
    """Per-parameter adaptive steps. Robust where hand-tuned SGD is fussy."""

    def __init__(self, params, lr, betas=(0.9, 0.999), eps=1e-8):
        self.params, self.lr, self.eps = params, lr, eps
        self.b1, self.b2 = betas
        self.m = [0.0] * len(params)
        self.v = [0.0] * len(params)
        self.t = 0

    def step(self, lr=None):
        self.t += 1
        lr = self.lr if lr is None else lr
        # bias correction, folded into the effective step size
        scale = lr * math.sqrt(1 - self.b2**self.t) / (1 - self.b1**self.t)
        for i, p in enumerate(self.params):
            g = p.grad
            self.m[i] = self.b1 * self.m[i] + (1 - self.b1) * g
            self.v[i] = self.b2 * self.v[i] + (1 - self.b2) * g * g
            p.data -= scale * self.m[i] / (math.sqrt(self.v[i]) + self.eps)

    def zero_grad(self):
        for p in self.params:
            p.grad = 0.0


def logistic_loss(net, batch):
    """softplus(-y * score): ~0 when confidently right, grows linearly when wrong."""
    total = Value(0.0)
    for point, label in batch:
        total = total + (net(point) * -float(label)).softplus()
    return total * (1.0 / len(batch))


def main():
    rng = random.Random(1234)
    data = two_spirals(n_per_class=90, turns=1.35, noise=0.035, rng=rng)
    net = MLP([2, 12, 12, 1], rng)
    opt = Adam(net.parameters(), lr=0.05)

    # Cost is steps x batch_size, but progress comes from *updates* -- so at a
    # fixed budget a tiny batch wins outright. bs=4/6000 hits 100%; bs=32/700,
    # same compute, stalls at 62%. (lr=0.1 diverges here, 0.05 is the ceiling.)
    steps, batch_size, peak_lr = 6000, 4, 0.05
    history, smooth = [], None

    print(f"\n  {len(data)} points · {len(opt.params)} parameters · {steps} Adam steps")
    print("  training (pure Python, no numpy — give it a minute)\n")

    for step in range(steps):
        loss = logistic_loss(net, rng.sample(data, batch_size))

        opt.zero_grad()
        loss.backward()
        lr = 0.0005 + (peak_lr - 0.0005) * 0.5 * (1 + math.cos(math.pi * step / steps))
        opt.step(lr)

        # a batch of 4 is far too noisy to read, so track an EMA instead
        smooth = loss.data if smooth is None else 0.99 * smooth + 0.01 * loss.data
        history.append(smooth)
        if step % 750 == 0 or step == steps - 1:
            print(f"  step {step:5d}   loss {smooth:.4f}   lr {lr:.4f}")

    correct = sum(1 for point, label in data if (net(point).data > 0) == (label > 0))
    print(f"\n  loss  {sparkline(history)}  {history[0]:.3f} → {history[-1]:.3f}")
    print(f"  full-set loss {logistic_loss(net, data).data:.4f}")
    print(f"  accuracy: {correct}/{len(data)} ({100 * correct / len(data):.1f}%)\n")
    render(net, data)
    print("  \x1b[38;5;214mO\x1b[0m / \x1b[38;5;39mX\x1b[0m are the data; "
          "shading is the network's confidence, \x1b[38;5;244m·\x1b[0m the boundary.\n")


def gradcheck():
    """Compare every analytic gradient against a central finite difference.

    Worth keeping runnable: when the net underfits, this is the first thing you
    want ruled out before you go tuning hyperparameters.
    """
    rng = random.Random(7)
    net = MLP([2, 5, 4, 1], rng)
    params = net.parameters()
    sample = [((0.3, -0.7), +1)]

    for p in params:
        p.grad = 0.0
    logistic_loss(net, sample).backward()
    analytic = [p.grad for p in params]

    eps, worst = 1e-6, 0.0
    for p, a in zip(params, analytic):
        origin = p.data
        p.data = origin + eps
        hi = logistic_loss(net, sample).data
        p.data = origin - eps
        lo = logistic_loss(net, sample).data
        p.data = origin
        numeric = (hi - lo) / (2 * eps)
        worst = max(worst, abs(a - numeric) / max(1e-9, abs(numeric)))

    print(f"  {len(params)} params · max relative error {worst:.2e}")
    print("  PASS\n" if worst < 1e-5 else "  FAIL\n")
    return worst < 1e-5


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if gradcheck() else 1)
    main()
