#!/usr/bin/env python3
# Copyright 2019 - 2026 Auspex Labs Inc.
# Licensed under the Apache License, Version 2.0
"""Markdown to RTF converter using mistune.

Provides both a Python API and CLI for converting Markdown to RTF format.
"""

import argparse
import sys

import mistune


# RTF font and color constants
FONTS = [
    ("Helvetica", "swiss"),
    ("Courier", "modern"),
]

# Colors: black, muted gray (blockquotes), blue (links)
COLORS = [
    (0, 0, 0),
    (102, 102, 102),
    (0, 102, 204),
]

DEFAULT_FONT_SIZE = 24  # half-points (12pt)

HEADING_SIZES = {
    1: 72,  # 36pt
    2: 56,  # 28pt
    3: 44,  # 22pt
    4: 36,  # 18pt
    5: 28,  # 14pt
    6: 24,  # 12pt
}


def escape_rtf(text):
    """Escape RTF special characters and handle Unicode."""
    result = []
    for ch in text:
        if ch == "\\":
            result.append("\\\\")
        elif ch == "{":
            result.append("\\{")
        elif ch == "}":
            result.append("\\}")
        elif ord(ch) > 127:
            result.append(f"\\u{ord(ch)}?")
        else:
            result.append(ch)
    return "".join(result)


def rtf_header():
    """Generate the RTF document header."""
    parts = ["{\\rtf1\\ansi\\ansicpg1252\\deff0"]
    # Font table
    parts.append("{\\fonttbl")
    for i, (name, family) in enumerate(FONTS):
        parts.append(f"{{\\f{i}\\f{family} {name};}}")
    parts.append("}")
    # Color table
    parts.append("{\\colortbl ;")
    for r, g, b in COLORS:
        parts.append(f"\\red{r}\\green{g}\\blue{b};")
    parts.append("}")
    # Default font size
    parts.append(f"\\fs{DEFAULT_FONT_SIZE}")
    parts.append("\n")
    return "".join(parts)


def render_block_code(token):
    """Render a fenced or indented code block."""
    raw = token.get("raw", "")
    text = escape_rtf(raw)
    text = text.replace("\n", "\\line\n")
    if text.endswith("\\line\n"):
        text = text[:-6]
    return f"\\pard\\li360\\ri360\\sa200\\f1\\fs20 " f"{text}\\f0\\fs{DEFAULT_FONT_SIZE}\\par\n"


def render_thematic_break(token):
    """Render a horizontal rule."""
    return "\\pard\\brdrb\\brdrs\\brdrw10\\brsp20 \\par\n\\pard\\sa200\\par\n"


def render_text(token):
    """Render a text node."""
    raw = token.get("raw", "")
    if raw is None:
        raw = ""
    return escape_rtf(raw)


def render_codespan(token):
    """Render inline code."""
    raw = token.get("raw", "")
    text = escape_rtf(raw)
    return f"{{\\f1 {text}}}"


def render_image(token):
    """Render an image as alt-text placeholder."""
    alt = token["attrs"].get("alt", "")
    if not alt:
        children = token.get("children")
        if children:
            alt = "".join(c.get("raw", "") for c in children if c["type"] == "text")
    return f"[Image: {escape_rtf(alt)}]"


def render_softbreak(token):
    """Render a soft line break as a space."""
    return " "


def render_linebreak(token):
    """Render a hard line break."""
    return "\\line\n"


def render_blank_line(token):
    """Render a blank line (no output)."""
    return ""


class RtfRenderer:
    """Walks a mistune AST and emits RTF."""

    def __init__(self):
        self.list_depth = 0
        self.ordered_counters = {}

    def render(self, tokens):
        """Render a list of AST tokens to RTF."""
        return "".join(self.render_token(t) for t in tokens)

    def render_token(self, token):
        match token["type"]:
            # Block elements
            case "paragraph":
                return self.render_paragraph(token)
            case "heading":
                return self.render_heading(token)
            case "block_code":
                return render_block_code(token)
            case "list":
                return self.render_list(token)
            case "block_quote":
                return self.render_block_quote(token)
            case "thematic_break":
                return render_thematic_break(token)
            case "blank_line":
                return render_blank_line(token)
            # Inline elements
            case "text":
                return render_text(token)
            case "strong":
                return self.render_strong(token)
            case "emphasis":
                return self.render_emphasis(token)
            case "codespan":
                return render_codespan(token)
            case "link":
                return self.render_link(token)
            case "image":
                return render_image(token)
            case "softbreak":
                return render_softbreak(token)
            case "linebreak":
                return render_linebreak(token)
            case "block_text":
                return self.render_block_text(token)
            case _:
                children = token.get("children")
                if children:
                    return self.render(children)
                return ""

    def render_children(self, token):
        children = token.get("children")
        if children:
            return self.render(children)
        raw = token.get("raw", "")
        return escape_rtf(raw) if raw else ""

    # Block elements

    def render_paragraph(self, token):
        content = self.render_children(token)
        return f"\\pard\\sa200\\f0\\fs{DEFAULT_FONT_SIZE} {content}\\par\n"

    def render_heading(self, token):
        level = token["attrs"]["level"]
        size = HEADING_SIZES.get(level, DEFAULT_FONT_SIZE)
        content = self.render_children(token)
        return f"\\pard\\sb360\\sa200\\f0\\fs{size}\\b " f"{content}\\b0\\par\n"

    def render_list(self, token):
        ordered = token["attrs"].get("ordered", False)
        self.list_depth += 1
        if ordered:
            self.ordered_counters[self.list_depth] = 0
        result = []
        children = token.get("children", [])
        for child in children:
            if ordered:
                self.ordered_counters[self.list_depth] += 1
            result.append(self.render_list_item(child, ordered))
        if ordered and self.list_depth in self.ordered_counters:
            del self.ordered_counters[self.list_depth]
        self.list_depth -= 1
        return "".join(result)

    def render_list_item(self, token, ordered=False):
        indent = self.list_depth * 720
        if ordered:
            num = self.ordered_counters.get(self.list_depth, 1)
            bullet = f"{num}."
        else:
            bullet = "\\bullet"
        parts = []
        children = token.get("children", [])
        first_block = True
        for child in children:
            if child["type"] == "list":
                parts.append(self.render_token(child))
            elif child["type"] in ("paragraph", "block_text"):
                content = self.render_children(child)
                if first_block:
                    parts.append(f"\\pard\\li{indent}\\fi-360\\sa100\\f0" f"\\fs{DEFAULT_FONT_SIZE} " f"{bullet} {content}\\par\n")
                    first_block = False
                else:
                    parts.append(f"\\pard\\li{indent}\\sa100\\f0" f"\\fs{DEFAULT_FONT_SIZE} " f"{content}\\par\n")
            else:
                parts.append(self.render_token(child))
        return "".join(parts)

    def render_block_quote(self, token):
        content = self.render_inner_blocks(token)
        return f"\\pard\\li720\\ri720\\sa200\\cf2\\i " f"{content}\\i0\\cf0\\par\n"

    def render_inner_blocks(self, token):
        """Render children but strip outer paragraph formatting."""
        children = token.get("children", [])
        parts = []
        for child in children:
            if child["type"] == "paragraph":
                parts.append(self.render_children(child))
            else:
                parts.append(self.render_token(child))
        return " ".join(parts)

    # Inline elements

    def render_strong(self, token):
        content = self.render_children(token)
        return f"{{\\b {content}}}"

    def render_emphasis(self, token):
        content = self.render_children(token)
        return f"{{\\i {content}}}"

    def render_link(self, token):
        url = token["attrs"].get("url", "")
        children = token.get("children")
        if children:
            text = self.render(children)
        else:
            text = escape_rtf(url)
        return f'{{\\field{{\\*\\fldinst{{HYPERLINK "{escape_rtf(url)}"}}}}' f"{{\\fldrslt{{\\cf3 {text}}}}}}}"

    def render_block_text(self, token):
        return self.render_children(token)


def convert(markdown_text):
    """Convert a Markdown string to an RTF string.

    Args:
        markdown_text: Input Markdown text.

    Returns:
        RTF-formatted string.
    """
    md = mistune.create_markdown(renderer="ast")
    tokens = md(markdown_text)
    renderer = RtfRenderer()
    body = renderer.render(tokens)
    return rtf_header() + body + "}"


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Convert Markdown to RTF.")
    parser.add_argument("input", nargs="?", default=None, help="Input Markdown file (reads stdin if omitted)")
    parser.add_argument("-o", "--output", default=None, help="Output RTF file path")
    parser.add_argument("--stdout", action="store_true", help="Print RTF to stdout instead of writing a file")
    args = parser.parse_args()

    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                md_text = f.read()
        except FileNotFoundError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        except PermissionError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
    else:
        try:
            md_text = sys.stdin.read()
        except IOError as err:
            print(f"Error reading stdin: {err}", file=sys.stderr)
            return 1

    try:
        rtf = convert(md_text)
    except Exception as err:
        print(f"Error converting markdown: {err}", file=sys.stderr)
        return 1

    if args.stdout:
        try:
            sys.stdout.write(rtf)
        except IOError as err:
            print(f"Error writing to stdout: {err}", file=sys.stderr)
            return 1
    else:
        out_path = args.output
        if not out_path:
            if args.input:
                if args.input.endswith(".md"):
                    out_path = args.input[:-3] + ".rtf"
                else:
                    out_path = args.input + ".rtf"
            else:
                print("Error: --output is required when reading from " "stdin without --stdout.", file=sys.stderr)
                return 1
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rtf)
        except PermissionError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        print(f"Wrote {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
