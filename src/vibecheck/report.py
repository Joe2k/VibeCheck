"""Write sections of reports/numbers.md. Each notebook owns one section."""

import re

from vibecheck.filter_sf import ROOT

NUMBERS_MD = ROOT / "reports" / "numbers.md"
HEADER = "# VibeCheck numbers\n\nWritten by the notebooks. Don't edit by hand.\n"


def write_section(name: str, markdown: str) -> None:
    """Replace (or append) the section between `<!-- name -->` markers in reports/numbers.md."""
    text = NUMBERS_MD.read_text(encoding="utf-8") if NUMBERS_MD.exists() else HEADER
    block = f"<!-- {name} -->\n{markdown.strip()}\n<!-- /{name} -->"
    pattern = re.compile(rf"<!-- {re.escape(name)} -->.*?<!-- /{re.escape(name)} -->", re.DOTALL)
    text = pattern.sub(lambda _: block, text) if pattern.search(text) else f"{text.rstrip()}\n\n{block}\n"
    NUMBERS_MD.parent.mkdir(parents=True, exist_ok=True)
    NUMBERS_MD.write_text(text, encoding="utf-8")  # not the OS default: Windows would use cp1252
