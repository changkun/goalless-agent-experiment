# jsonq

A small, dependency-free Python CLI for querying and formatting JSON.

## Usage

```
usage: jsonq [-h] [-q PATH] [-f PATH=EXPECT] [-i] [--indent INDENT] [file]
```

Read JSON from a file (or stdin with `-` / no file argument):

```sh
# Pretty-print
echo '{"a":1,"b":[1,2]}' | ./jsonq.py

# Extract a value by dot-path (supports list indices: foo.bar[0].baz)
./jsonq.py data.json -q users[0].name

# Filter a list: print items where PATH equals EXPECT
./jsonq.py data.json -f role=admin

# Filter and print just the matched value
./jsonq.py data.json -f active=true -i

# Custom indent
./jsonq.py data.json --indent 4
```

If the root JSON is a list, `-f` filters its items. Otherwise `-f` treats the
whole document as the item to test against the path.

`EXPECT` is parsed as JSON when possible, so `-f n=1` matches the number `1`
and `-f n=true` matches the boolean `true`. Use quotes (e.g. `-f n='"1"'`) to
match a string explicitly.

## Tests

```sh
python3 -m unittest test_jsonq
```
