# wfc

Wave Function Collapse texture synthesis for the terminal, in one dependency-free
Python file.

You hand it a small hand-drawn ASCII sample. It learns every N×N patch in that
sample and which patches may sit beside which, then grows a new image that is
locally indistinguishable from the original but globally novel.

```
$ ./wfc.py islands -W 64 -H 20 -s 7
~~~,.^^^^.,~~,.^^^.,~~~~~~~~~~~~~,.^^^^^^^^^^^^^.,~~~~~~~~~,...,
~~~,..^^..,~~~,...,~~~~~~~~~~~~~~,..^^^..^^^^^^^^.,,~~~~~~~~,,~~
~~~~,....,,~~~,,.,~~~~~~~~~~~~~~~,,........^^^^^^..,,~~~~~~~~~~~
~~~~~,,,,,~~~~~,,~~~~~~,,,,,~~~~~~,,,,,,,,...^^^^^..,~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~,,.....,~~~~~~~~~~~~~,,...^^..,~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~,...^^^..,~~~~~~~~~~~~~~,,....,~~~~~~~~~~~,,
~~~~~~~~~~~~~~~~~~~,..^^^^^^.,~~~~~~~~~~~~~~~~,,,,~~~~~~~~~~~,..
```

Nobody wrote the rule "beaches ring the grass, peaks stay inland." That falls
out of the sample's 3×3 patches on its own.

## Usage

```
./wfc.py --list                       # the five built-in samples
./wfc.py cave -W 80 -H 30             # generate
./wfc.py flowers --sample-art         # see what it learned from
./wfc.py cave -p                      # output that tiles seamlessly
./wfc.py islands -n 4 -s 12           # bigger patches, fixed seed
```

`islands` · `cave` · `circuit` · `flowers` · `rooms`

## Adding a sample

Drop an entry in `SAMPLES`. Keep it small — 10×20 is plenty.

- `symmetry` — `1` as drawn, `2` mirrored, `4` rotated, `8` full dihedral. Use
  4 or 8 only when the glyphs themselves survive rotation: `#` does, `─` does not.
- `periodic` — harvest patches across the sample's edges, as a torus.
- `ground` — pin a floor at the bottom and sky at the top, for samples that only
  read correctly one way up.
- `palette` — glyph to xterm-256 colour.

## How it works

1. **Harvest** every N×N patch of the sample, with its frequency, plus its
   dihedral variants.
2. **Compatibility** — patch *a* may sit left of *b* iff their 2-column overlap
   agrees. Stored as bitmasks, one per direction per patch.
3. **Observe** the undecided cell with the lowest Shannon entropy over its
   weighted options, and collapse it to one patch — likelier patches first.
4. **Propagate** with a worklist: a neighbour keeps only the patches some
   surviving option permits. Repeat until stable.
5. **Backtrack** when a cell empties. Each choice is a frame holding the wave
   as it was and the options not yet tried, so a dead end walks back instead of
   restarting.

Rendering reads one glyph per cell out of its chosen patch — the top-left,
except along a non-wrapping edge, where there is no cell beyond and it steps
into the interior of the last usable patch instead.

## Tests

```
python3 test_wfc.py
```

The one that matters is local validity: harvest the *output* and assert it
introduced no patch the sample never contained. That is the whole contract, and
it is checked for every sample, at N = 2, 3 and 4, periodic and not, down to
grids as small as a single patch.
