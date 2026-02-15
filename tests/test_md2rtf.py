# Copyright 2019 - 2026 Auspex Labs Inc.
# Licensed under the Apache License, Version 2.0
"""Tests for md2rtf converter."""

import os

import pytest

from md2rtf import convert


TEST_MD_PATH = os.path.join(os.path.dirname(__file__), "test.md")


@pytest.fixture
def test_md():
    with open(TEST_MD_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def test_rtf(test_md):
    return convert(test_md)


def test_rtf_starts_correctly(test_rtf):
    assert test_rtf.startswith("{\\rtf1")


def test_braces_balanced(test_rtf):
    depth = 0
    for ch in test_rtf:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        assert depth >= 0, "Closing brace before matching open brace"
    assert depth == 0, f"Unbalanced braces: depth ended at {depth}"


def test_has_font_table(test_rtf):
    assert "\\fonttbl" in test_rtf


def test_has_color_table(test_rtf):
    assert "\\colortbl" in test_rtf


def test_has_bold(test_rtf):
    assert "\\b " in test_rtf


def test_has_italic(test_rtf):
    assert "\\i " in test_rtf


def test_has_bullet_list(test_rtf):
    assert "\\bullet" in test_rtf


def test_has_hyperlink(test_rtf):
    assert "HYPERLINK" in test_rtf


def test_has_monospace(test_rtf):
    assert "\\f1 " in test_rtf


def test_empty_input():
    rtf = convert("")
    assert rtf.startswith("{\\rtf1")
    assert rtf.endswith("}")


def test_plain_text():
    rtf = convert("Hello world")
    assert "Hello world" in rtf


def test_special_chars_escaped():
    rtf = convert("Braces { } and backslash \\")
    assert "\\{" in rtf
    assert "\\}" in rtf
    assert "\\\\" in rtf


def test_unicode():
    rtf = convert("caf\u00e9")
    assert "\\u233?" in rtf


def test_hard_line_break():
    rtf = convert("first line\\\nsecond line")
    assert "\\line" in rtf
