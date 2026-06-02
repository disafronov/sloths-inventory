"""Validate .po file integrity — no fuzzy entries, matching placeholders."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent.parent.parent
PO_GLOBS = sorted(BASE.glob("src/*/locale/*/LC_MESSAGES/django.po"))


@pytest.mark.parametrize("po_path", PO_GLOBS, ids=lambda p: str(p.relative_to(BASE)))
def test_no_fuzzy_entries(po_path: Path) -> None:
    """No individual translation entry should be marked fuzzy.

    The header ``#, fuzzy`` (line 6) is exempt — it only flags metadata.
    """
    content = po_path.read_text(encoding="utf-8")
    # Split into entries (separated by blank lines between entries).
    # The header is the first entry; skip it.
    entries = re.split(r"\n\n(?!\s*#~)", content)

    for i, entry in enumerate(entries):
        if i == 0:
            continue  # header
        if entry.lstrip().startswith("#~"):
            continue  # commented-out (obsolete) entry
        if "#, fuzzy" in entry:
            # Extract msgid for a helpful message
            m = re.search(r'msgid\s+"(.*?)"', entry, re.DOTALL)
            msgid = m.group(1).replace('""\n', "") if m else "(unknown)"
            pytest.fail(
                f"{po_path.relative_to(BASE)}: fuzzy entry #{i}: msgid={msgid!r}"
            )


_PLACEHOLDER_RE = re.compile(r"%\(\w+\)s")


@pytest.mark.parametrize("po_path", PO_GLOBS, ids=lambda p: str(p.relative_to(BASE)))
def test_placeholder_match(po_path: Path) -> None:
    """Placeholders in msgid must match msgstr."""

    content = po_path.read_text(encoding="utf-8")
    entries = re.split(r"\n\n(?!\s*#~)", content)

    for i, entry in enumerate(entries):
        if i == 0:
            continue  # header
        if entry.lstrip().startswith("#~"):
            continue  # commented-out (obsolete) entry

        msgid_match = re.search(r'^msgid\s+"(.*?)"$', entry, re.MULTILINE | re.DOTALL)
        if not msgid_match:
            continue
        msgid = _concat_po_string(msgid_match.group(1))

        msgstr_match = re.search(r'^msgstr\s+"(.*?)"$', entry, re.MULTILINE | re.DOTALL)
        if not msgstr_match:
            continue
        msgstr = _concat_po_string(msgstr_match.group(1))

        id_placeholders = sorted(_PLACEHOLDER_RE.findall(msgid))
        str_placeholders = sorted(_PLACEHOLDER_RE.findall(msgstr))

        if id_placeholders != str_placeholders:
            pytest.fail(
                f"{po_path.relative_to(BASE)}: placeholder mismatch in entry #{i}\n"
                f"  msgid: {msgid!r}\n"
                f"  msgid placeholders: {id_placeholders}\n"
                f"  msgstr: {msgstr!r}\n"
                f"  msgstr placeholders: {str_placeholders}"
            )


def _concat_po_string(raw: str) -> str:
    """Concatenate multi-line PO string (removing internal quotes/newlines)."""
    # Remove the enclosing quotes and join consecutive string fragments
    # e.g. `""\n"foo %(bar)s"\n"baz"` → `foo %(bar)s baz`
    fragments = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
    return "".join(fragments)
