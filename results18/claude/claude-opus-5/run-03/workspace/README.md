# wfc-ascii

Wave Function Collapse for ASCII textures. Give it a small hand-drawn sample and it
synthesises a larger grid in which **every NxN window also occurs in the sample** —
locally indistinguishable from the input, globally novel.

Pure standard library, Python 3.10+.

```
python3 cli.py                       # 72x20 island, random seed
python3 cli.py cave -w 100 -H 30
python3 cli.py circuit --show-sample -s 5
python3 cli.py maze --periodic       # output tiles seamlessly
python3 cli.py all --no-color
python3 cli.py --list
```

Sample output (`circuit`, seed 5) — note that every junction glyph still connects
correctly, because a mis-wired junction is a 3x3 window that never appeared in the
sample and so is unreachable by construction:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛···╻··························
·································┃··························
······························┏━━┛··························
······························╹·····························
·································███████████████████████████
···╻·····························███████████████████████████
···┃·······················╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
━━━┛························································
····························································
····┏━━━━━━━━━┓·············································
····╹·········┃··········╺━━━━━┓····························
··············┣━━┓·············┃······╺━━━━━━━━━━━━━━━━━━━━━
··············┃··┃·············┣━━┓·························
········╺━━━━━┛··┣━━┓··········┃··┃·························
```

## How it works

`wfc.py` implements Gumin's overlapping model.

1. **Extract.** Slide an NxN window over the sample, optionally wrapping at the
   edges (`periodic_input`) and including dihedral variants (`symmetry`). Each
   distinct window is a *pattern*; its occurrence count is its weight.
2. **Adjacency.** Patterns `a` and `b` may be neighbours in direction `d` if their
   `N x (N-1)` overlap agrees character for character. This is `propagator[d][a]`.
3. **Superpose.** Every output cell starts as the set of all patterns.
4. **Observe.** Collapse the cell with the lowest Shannon entropy — the one
   closest to decided — picking a pattern with probability proportional to weight.
   Ties get a tiny jitter so the scan does not bias toward low indices.
5. **Propagate.** Maintain `support[cell][pattern][d]`: how many patterns still
   alive in the neighbour at `d` would permit this pattern here. Banning a pattern
   decrements its neighbours' counts; a count reaching zero bans that pattern too,
   cascading. This is arc consistency with incremental counters, so propagation is
   linear in the number of removals rather than quadratic in patterns.
6. **Repeat** until every cell is decided. If a cell runs out of patterns the draw
   was unlucky — restart with a fresh seed (up to `attempts`).

### Two subtleties worth knowing

**Symmetry does not rotate glyphs.** The dihedral variants rearrange characters
within the window; they do not remap them. A rotated run of `━` is a *vertical*
run of horizontal glyphs. So only orientation-free character sets (`#`, `~`, `░`)
may use `symmetry=8`; anything using box-drawing must use `symmetry=1`. Getting
this wrong produces output that is technically valid and visually nonsense.

**Starved patterns must be banned up front.** A pattern extracted from a
non-periodic sample can have an *empty* propagator entry — nothing may legally
follow it that way. Its support count starts at zero, so it can never *reach*
zero, and the propagate loop would never remove it. `Wave._seed_unsupported`
bans these before the first observation. Without it, degenerate samples "succeed"
with output that violates the adjacency rules.

**Boundaries are unconstrained.** With `periodic_output=False` an edge cell simply
has fewer neighbours, so anything the sample allows to run off the edge will. In
`meadow` you will occasionally see a stem reaching the top of the frame with no
flower on it, and in `circuit` a trace leaving the frame without a terminator.
Both are locally legal — the sample contains mid-stem and mid-trace windows — and
the only fix is to constrain the border explicitly, which this does not do.

## API

```python
from wfc import generate

rows = generate(
    ["~~~~", "~##~", "~##~", "~~~~"],  # sample
    width=60, height=20,
    size=3,                  # pattern size N
    symmetry=8,              # 1 = as drawn, 8 = full dihedral group
    periodic_input=True,     # wrap the sample when extracting patterns
    periodic_output=False,   # make the result tileable
    seed=None,
    attempts=40,
)                            # -> list[str], or raises Contradiction
```

## Tests

```
python3 -m unittest test_wfc -v
```

The load-bearing test is `test_every_window_occurs_in_the_sample`, which
re-derives the pattern set and checks every window of the output against it, for
every shipped sample. It is the whole contract in one assertion, and it caught a
transposed direction index in the support-count initialiser that had made every
asymmetric sample unsolvable while leaving symmetric ones looking fine.

## Notes

Cost is dominated by `lowest_entropy_cell`, a linear scan per observation, so
generation is O(cells²) in the worst case — about 0.8 s for a full 56x18 screen
with ~350 patterns. A lazy heap would help; the scan is kept for clarity, and
matches the reference implementation.

Restart-on-contradiction rather than backtracking is also the reference
behaviour. Across 25 seeds for each of the six samples at 56x18, no generation
needed a restart.
