# md2rtf

A lightweight Python module that converts Markdown to RTF (Rich Text Format). It uses [mistune](https://github.com/lepture/mistune) v3.x to parse Markdown into an AST, then walks the tree to emit valid RTF output.

## Supported Markdown Elements

| Element | RTF Output |
|---|---|
| Headings (h1-h6) | Scaled font sizes (36pt down to 12pt), bold, paragraph spacing |
| Paragraphs | Default font with spacing after |
| Bold / Italic / Bold+Italic | `\b`, `\i`, nested combinations |
| Inline code | Monospace font (Courier) |
| Code blocks | Monospace font, preserved line breaks, indented |
| Links | RTF HYPERLINK fields with blue color |
| Images | Rendered as `[Image: alt text]` placeholder |
| Unordered lists | Bullet character with hanging indent, nested up to 3+ levels |
| Ordered lists | Sequential numbers with hanging indent, nested up to 3+ levels |
| Blockquotes | Indented, italic, muted gray color |
| Horizontal rules | Bottom border paragraph |
| Line breaks | Hard and soft breaks |

## Requirements

- Python 3.10+
- mistune 3.x

## Installation

```
pip install -r requirements.txt
```

## Usage

### Python API

```python
from md2rtf import convert

rtf_string = convert("# Hello\n\nSome **bold** text.")
```

### CLI

Convert a file (output defaults to same name with `.rtf` extension):

```
python md2rtf.py input.md
```

Specify an output path:

```
python md2rtf.py input.md -o output.rtf
```

Print RTF to stdout:

```
python md2rtf.py input.md --stdout
```

Read from stdin:

```
cat input.md | python md2rtf.py --stdout
```

## Testing

```
pip install pytest
pytest tests/
```

## Project Structure

```
md2rtf.py              Main module (converter + CLI)
requirements.txt       Python dependencies
tests/
    test_md2rtf.py     pytest test suite
    test.md            Test fixture exercising all supported elements
    test.rtf           Reference RTF output
```

## License

Copyright 2019 - 2026 Auspex Labs Inc. Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
