# lifegrid

Your life as a grid of weeks. One dot per week — columns are the weeks of a year,
rows are years. See at a glance how much of the box you've filled.

```
●  lived    ●  today    ●  to go
33.4 years lived · 2,943 weeks left (to age 90) · 37.1% of the grid filled
```

## Usage

```sh
./lifegrid.py --born 1993-04-15            # from a date of birth
./lifegrid.py --age 31.5                   # or just your age in years
./lifegrid.py --born 1993-04-15 --until 80 # stop at age 80 instead of 90
./lifegrid.py --age 31.5 | cat             # piped output auto-switches to plain
```

Pure Python stdlib, zero dependencies. When stdout isn't a TTY it falls back to a
plain `#`/`.`/`T` grid so pipes and redirection stay clean.
