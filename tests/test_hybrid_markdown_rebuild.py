"""Tests for hybrid markdown text rebuild behavior."""

from pdf_converter.hybrid.core import _replace_table_spans_in_markdown, _rebuild_page_text


def test_replace_table_spans_preserves_non_table_text():
    """Only table spans are replaced; surrounding markdown stays untouched."""
    original = "Intro\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n\nOutro\n"
    table_start = original.index("| A | B |")
    table_src = "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
    table_end = table_start + len(table_src)

    replacement = "| X | Y |\n| --- | --- |\n| 3 | 4 |\n"
    page_data = {
        "text": original,
        "page_boxes": [
            {"index": 0, "class": "text", "pos": [0, table_start]},
            {
                "index": 1,
                "class": "table",
                "pos": [table_start, table_end],
                "text": replacement,
            },
            {"index": 2, "class": "text", "pos": [table_end, len(original)]},
        ],
    }

    rebuilt = _replace_table_spans_in_markdown(page_data)
    assert rebuilt == original[:table_start] + replacement + original[table_end:]


def test_replace_table_spans_invalid_pos_falls_back_to_original():
    """Invalid table spans should not corrupt markdown text."""
    original = "Before\n\n| A |\n| --- |\n| 1 |\n\nAfter\n"
    page_data = {
        "text": original,
        "page_boxes": [
            {
                "index": 0,
                "class": "table",
                "pos": [1000, 1010],
                "text": "| B |\n| --- |\n| 2 |\n",
            }
        ],
    }

    rebuilt = _replace_table_spans_in_markdown(page_data)
    assert rebuilt == original


def test_rebuild_page_text_md_uses_pos_based_replacement():
    """Markdown rebuild should use page text and table pos ranges."""
    original = "Alpha\n\n| H |\n| --- |\n| V |\n\nOmega\n"
    table_start = original.index("| H |")
    table_src = "| H |\n| --- |\n| V |\n"
    table_end = table_start + len(table_src)
    replacement = "| R |\n| --- |\n| S |\n"

    page_data = {
        "text": original,
        "page_boxes": [
            {
                "index": 3,
                "class": "table",
                "bbox": [10, 20, 30, 40],
                "pos": [table_start, table_end],
                "text": replacement,
            }
        ],
        "metadata": {"page_number": 1},
    }

    rebuilt = _rebuild_page_text(page_data, "md")
    assert rebuilt == original[:table_start] + replacement + original[table_end:]
