"""
Turn tagged Māori verses into output files.

Outputs:
    tagged_output.txt
        Plain word/tag output.

    tagged_output.html
        Colour-coded HTML output.

Run:
    python output.py

The default input and output paths are relative to this file, so the script
works regardless of the terminal's current working directory.
"""

from __future__ import annotations

import html
from pathlib import Path

from tagger_rules import tag_verses


BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Reconstruct verses and punctuation
# ---------------------------------------------------------------------------

def _verse_tokens(
    grouped: list[dict],
) -> list[tuple[int, list[dict]]]:
    """Group tagged tokens by verse.

    Punctuation following a word is attached to that word. Punctuation at the
    beginning of a verse is retained as a prefix on the first word.
    """
    verses: dict[int, list[dict]] = {}
    order: list[int] = []
    pending_prefix: dict[int, str] = {}

    for part in grouped:
        verse_id = part["verse_id"]

        if verse_id not in verses:
            verses[verse_id] = []
            pending_prefix[verse_id] = ""
            order.append(verse_id)

        if part["type"] == "punct":
            if verses[verse_id]:
                verses[verse_id][-1]["suffix"] += part["text"]
            else:
                pending_prefix[verse_id] += part["text"]

            continue

        for index, word in enumerate(part["display_words"]):
            prefix = ""

            if pending_prefix[verse_id]:
                prefix = pending_prefix[verse_id]
                pending_prefix[verse_id] = ""

            verses[verse_id].append({
                "word": word,
                "tag": part["tags"][index],
                "prefix": prefix,
                "suffix": "",
            })

    # Preserve any punctuation left at the end of a verse.
    for verse_id, punctuation in pending_prefix.items():
        if punctuation and verses[verse_id]:
            verses[verse_id][-1]["suffix"] += punctuation

    return [
        (verse_id, verses[verse_id])
        for verse_id in order
    ]


# ---------------------------------------------------------------------------
# Plain text output
# ---------------------------------------------------------------------------

def build_tagged_text(grouped: list[dict]) -> list[str]:
    """Build one numbered word/tag line per verse."""
    lines: list[str] = []

    for verse_id, tokens in _verse_tokens(grouped):
        rendered_tokens = []

        for token in tokens:
            rendered_tokens.append(
                f"{token['prefix']}"
                f"{token['word']}/{token['tag']}"
                f"{token['suffix']}"
            )

        lines.append(
            f"{verse_id + 1}: {' '.join(rendered_tokens)}"
        )

    return lines


def write_text(
    lines: list[str],
    path: str | Path,
) -> None:
    """Write plain tagged output using UTF-8."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

TAG_COLOURS = {
    "prep": "#d9e6ff",
    "nucl": "#d6f5d6",
    "post": "#fff0b3",
    "prep-nucl": "#d9e6ff",
    "nucl-post": "#e8d6ff",
    "prep-post": "#ffe0b3",
    "prep-nucl-post": "#eeeeee",
    "unk": "#eeeeee",
}


DISPLAY_LABELS = {
    "prep": "PREP",
    "nucl": "NUCL",
    "post": "POST",
    "prep-nucl": "PREP/NUCL",
    "nucl-post": "NUCL/POST",
    "prep-post": "PREP/POST",
    "prep-nucl-post": "PREP/NUCL/POST",
    "unk": "UNK",
}


HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Māori nucleus/periphery tagging</title>
<style>
  body {
    font-family: Arial, sans-serif;
    padding: 20px;
  }

  .legend {
    margin-bottom: 24px;
  }

  .legend-item {
    display: inline-block;
    margin-right: 12px;
  }

  .verse-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 18px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 12px;
  }

  .verse-id {
    width: 60px;
    font-weight: bold;
    color: #555;
    padding-top: 18px;
  }

  .tokens {
    flex: 1;
    line-height: 2.4;
  }

  .token {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    margin: 6px 5px;
    padding: 2px 3px;
    min-width: 28px;
  }

  .tag {
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
    padding: 3px 6px;
    border-radius: 6px;
    margin-bottom: 3px;
  }

  .word {
    font-size: 16px;
    color: #111;
  }
</style>
</head>
<body>
<h1>Māori nucleus/periphery tagging</h1>
<div class="legend">
  <span class="legend-item"><strong>PREP:</strong> preposed periphery</span>
  <span class="legend-item"><strong>NUCL:</strong> nucleus</span>
  <span class="legend-item"><strong>POST:</strong> postposed periphery</span>
</div>
"""


def build_html(grouped: list[dict]) -> str:
    """Build the complete colour-coded HTML document."""
    parts = [HTML_HEAD]

    for verse_id, tokens in _verse_tokens(grouped):
        parts.append(
            f'<div class="verse-row">'
            f'<div class="verse-id">{verse_id + 1}</div>'
            f'<div class="tokens">'
        )

        for token in tokens:
            tag = token["tag"]

            label = DISPLAY_LABELS.get(
                tag,
                tag.upper(),
            )

            colour = TAG_COLOURS.get(
                tag,
                "#dddddd",
            )

            displayed_word = (
                html.escape(token["prefix"])
                + html.escape(token["word"])
                + html.escape(token["suffix"])
            )

            parts.append(
                '<span class="token">'
                f'<span class="tag" style="background:{colour};">'
                f'{html.escape(label)}'
                '</span>'
                f'<span class="word">{displayed_word}</span>'
                '</span>'
            )

        parts.append("</div></div>")

    parts.append("</body></html>")

    return "\n".join(parts)


def write_html(
    grouped: list[dict],
    path: str | Path,
) -> None:
    """Write colour-coded HTML using UTF-8."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        build_html(grouped),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Run the pipeline
# ---------------------------------------------------------------------------

def run(
    input_path: str | Path | None = None,
    text_out: str | Path | None = None,
    html_out: str | Path | None = None,
) -> tuple[list[dict], list[dict]]:
    """Read the input, tag it, and write text and HTML outputs."""
    input_path = (
        Path(input_path)
        if input_path is not None
        else BASE_DIR / "train_sentences.txt"
    )

    text_out = (
        Path(text_out)
        if text_out is not None
        else BASE_DIR / "tagged_output_test.txt"
    )

    html_out = (
        Path(html_out)
        if html_out is not None
        else BASE_DIR / "tagged_output_test.html"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as input_file:
        verses = [
            line.strip()
            for line in input_file
            if line.strip()
        ]

    grouped, log = tag_verses(verses)

    write_text(
        build_tagged_text(grouped),
        text_out,
    )

    write_html(
        grouped,
        html_out,
    )

    print(
        f"Tagged {len(verses)} verses; "
        f"applied {len(log)} contextual rule changes."
    )
    print(f"Wrote text output: {text_out}")
    print(f"Wrote HTML output: {html_out}")

    return grouped, log


if __name__ == "__main__":
    run()

