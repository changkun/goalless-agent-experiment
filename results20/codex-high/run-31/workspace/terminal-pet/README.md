# Terminal Pet

A tiny, dependency-free virtual pet that lives in your terminal.

## Run it

```bash
./pet.py            # check on your pet
./pet.py feed       # give it a snack
./pet.py play       # toss a ball
./pet.py sleep      # tuck it in
./pet.py wake       # wake it up
```

## How it works

- Your pet grows from an egg → baby → adult as it ages.
- Stats (`happiness`, `fullness`, `energy`) drift each turn and react to your actions.
- Everything is random toy state per run in this demo; real projects would persist state to a file.
