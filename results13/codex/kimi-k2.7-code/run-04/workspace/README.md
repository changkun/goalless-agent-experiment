# treesize

A tiny CLI that prints a directory tree with human-readable sizes.

## Usage

```bash
python3 treesize.py /path/to/dir
python3 treesize.py -d 2              # limit depth
python3 treesize.py --no-files        # directories only
python3 treesize.py -l 10             # top 10 largest files
```

## Example

```
  4.2M  project
  ├── 512.0K  src
  │   ├──  12.3K  main.py
  │   └── 499.7K  data.csv
  └── 3.7M  dist
```
