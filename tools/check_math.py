"""Check that maths in the Markdown files renders the same everywhere.

GitHub, VS Code and the common static-site generators (MkDocs, Docusaurus,
markdown-it + KaTeX) all understand ``$inline$`` and ``$$`` display blocks,
but only a common subset of what can go inside them survives every Markdown
parser.  This script enforces that subset:

* display maths sits between ``$$`` lines of its own, with blank lines around;
* no backslash followed by punctuation (``\\,`` ``\\{`` ``\\\\`` ...), which
  Markdown may treat as an escape and strip before the maths is typeset;
* inline maths is not glued to a following letter or digit, and does not
  contain ``|`` (which would split a table cell).

Run ``python tools/check_math.py`` to lint, or with ``--dump`` to print every
expression as JSON (used to typeset them all with KaTeX as a second check).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / "blog").glob("*.md")),
]

FENCE = re.compile(r"^```.*?^```[^\n]*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE = re.compile(r"(?<!\$)\$(?!\$)([^$]+?)\$(?!\$)")
FRAGILE = re.compile(r"\\[^A-Za-z\s]")


def blank(match: re.Match) -> str:
    """Replace a match with spaces, keeping newlines so line numbers survive."""
    return re.sub(r"[^\n]", " ", match.group(0))


def expressions(text: str):
    """Yield ``(line, kind, tex)`` for every maths expression in ``text``."""
    text = INLINE_CODE.sub(blank, FENCE.sub(blank, text))
    for match in DISPLAY.finditer(text):
        yield text.count("\n", 0, match.start()) + 1, "display", match.group(1).strip()
    for match in INLINE.finditer(DISPLAY.sub(blank, text)):
        yield text.count("\n", 0, match.start()) + 1, "inline", match.group(1)


def lint(path: Path) -> list[str]:
    text = path.read_text()
    stripped = INLINE_CODE.sub(blank, FENCE.sub(blank, text))
    lines = stripped.split("\n")
    problems = []

    def report(line: int, message: str) -> None:
        problems.append(f"{path.relative_to(ROOT)}:{line}: {message}")

    for line, kind, tex in expressions(text):
        if found := FRAGILE.search(tex):
            report(line, f"backslash-punctuation {found.group(0)!r} in ${tex}$")
        if kind == "inline":
            if tex != tex.strip():
                report(line, f"space just inside the dollars of ${tex}$")
            if "|" in tex:
                report(line, f"'|' in inline maths ${tex}$ (use \\vert or \\mid)")

    for match in INLINE.finditer(DISPLAY.sub(blank, stripped)):
        following = stripped[match.end() : match.end() + 1]
        if following.isalnum():
            line = stripped.count("\n", 0, match.start()) + 1
            report(line, f"inline maths glued to {following!r}: {match.group(0)}")

    inside = False
    for number, line in enumerate(lines, 1):
        if "$$" not in line:
            continue
        if line != "$$":
            report(number, "'$$' must be alone on its line, unindented")
            continue
        neighbour = lines[number] if inside else lines[number - 2]
        if (number < len(lines) if inside else number > 1) and neighbour.strip():
            report(number, "display maths needs a blank line before and after")
        inside = not inside
    if inside:
        report(len(lines), "unclosed '$$'")
    if DISPLAY.sub("", stripped).count("$") % 2:
        report(1, "odd number of '$' outside display maths")
    return problems


def main() -> int:
    if "--dump" in sys.argv:
        dump = [
            {
                "file": str(path.relative_to(ROOT)),
                "line": line,
                "display": kind == "display",
                "tex": tex,
            }
            for path in FILES
            for line, kind, tex in expressions(path.read_text())
        ]
        json.dump(dump, sys.stdout)
        return 0
    problems = [problem for path in FILES for problem in lint(path)]
    print("\n".join(problems) if problems else f"maths OK in {len(FILES)} files")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
