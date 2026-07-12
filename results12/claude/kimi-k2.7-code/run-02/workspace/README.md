# Serendipity

A tiny CLI for random curiosity prompts and micro-adventures.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Get a random prompt
serendipity

# Filter by category
serendipity --category create

# List all prompts
serendipity --list

# Use custom prompts
serendipity --file prompts.json
```

## Custom prompts

Create a JSON file with this shape:

```json
[
  {
    "category": "wonder",
    "text": "Invent a word for a feeling you had today.",
    "why": "Naming an experience makes it shareable."
  }
]
```

Categories: `observe`, `create`, `connect`, `move`, `wonder`.

## Test

```bash
pytest
```
