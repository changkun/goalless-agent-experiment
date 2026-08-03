# pagepress

A minimal, dependency-free static site generator written in pure Python.
Feed it a Markdown file and get a clean, styled HTML page.

## Usage

```sh
python -m pip install -e .
pagepress example/index.md -o example/index.html
```

Or run without installing:

```sh
python -m pagepress example/index.md -o example/index.html
```

Pipe from stdin:

```sh
echo "# Hi" | pagepress
```

## Supported Markdown

- Headings `#` – `######`
- Fenced code blocks with language tags
- Ordered and unordered lists
- Inline `code`, **bold**, *emphasis*, and [links](...)
- Blockquotes and horizontal rules

## CLI

| Flag | Description |
| --- | --- |
| `input` | Markdown file (reads stdin if omitted) |
| `-o, --output` | Output HTML file (stdout if omitted) |
| `-t, --title` | Fallback title when no `# H1` exists |

## Project layout

```text
pagepress/
├── src/pagepress/     # Package: parser, CLI, stylesheet
├── tests/             # Unit tests (pure unittest)
├── example/           # Demo Markdown content
└── pyproject.toml     # Packaging / entry point
```

## Running tests

```sh
python -m unittest discover -s tests
```
