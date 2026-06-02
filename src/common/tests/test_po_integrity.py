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
    entries = _split_entries(content)

    for i, entry in enumerate(entries):
        if i == 0:
            continue  # header
        if entry.lstrip().startswith("#~"):
            continue  # commented-out (obsolete) entry
        if "#, fuzzy" in entry:
            msgid = _extract_po_string(entry, "msgid") or "(unknown)"
            pytest.fail(
                f"{po_path.relative_to(BASE)}: fuzzy entry #{i}: msgid={msgid!r}"
            )


@pytest.mark.parametrize("po_path", PO_GLOBS, ids=lambda p: str(p.relative_to(BASE)))
def test_no_redundant_msgstr(po_path: Path) -> None:
    """For English locale files, ``msgstr`` must not duplicate ``msgid``.

    When the translation equals the source string, leave ``msgstr ""`` so
    gettext falls through to ``msgid`` (the identity-translation convention).
    A non-empty copy is redundant.
    """
    locale = po_path.parent.parent.name
    if locale != "en":
        pytest.skip("only relevant for English locale .po files")

    content = po_path.read_text(encoding="utf-8")
    entries = _split_entries(content)

    for i, entry in enumerate(entries):
        if i == 0:
            continue  # header
        if entry.lstrip().startswith("#~"):
            continue  # obsolete

        msgid = _extract_po_string(entry, "msgid")
        msgstr = _extract_po_string(entry, "msgstr")
        if msgid is None or msgstr is None:
            continue
        if msgstr != "" and msgid == msgstr:
            pytest.fail(
                f"{po_path.relative_to(BASE)}: redundant msgstr in entry #{i}\n"
                f"  msgid:  {msgid!r}\n"
                f"  msgstr: {msgstr!r}\n"
                f"  Remove msgstr or leave it empty to inherit from msgid."
            )


# Match ``%(name)X`` — captures the variable *name*, ignores the format type.
_PLACEHOLDER_RE = re.compile(r"%\((\w+)\)")


@pytest.mark.parametrize("po_path", PO_GLOBS, ids=lambda p: str(p.relative_to(BASE)))
def test_placeholder_match(po_path: Path) -> None:
    """Placeholders in msgid must match msgstr (including plurals: msgstr[N]).

    For English locale files empty ``msgstr ""`` (identity translation) is
    valid — placeholders are inherited from msgid.
    """

    content = po_path.read_text(encoding="utf-8")
    locale = po_path.parent.parent.name
    entries = _split_entries(content)

    for i, entry in enumerate(entries):
        if i == 0:
            continue  # header
        if entry.lstrip().startswith("#~"):
            continue  # obsolete

        msgid = _extract_po_string(entry, "msgid")
        if msgid is None:
            continue

        # Collect unique placeholders from msgid (+ msgid_plural if present)
        id_vars: set[str] = set(_PLACEHOLDER_RE.findall(msgid))
        msgid_plural = _extract_po_string(entry, "msgid_plural")
        if msgid_plural is not None:
            id_vars.update(_PLACEHOLDER_RE.findall(msgid_plural))

        # Check every msgstr variant (msgstr, msgstr[0], msgstr[1], …)
        markers = re.findall(
            r"^(msgstr(?:\[\d+\])?)\s+",
            entry,
            re.MULTILINE,
        )
        if not markers:
            continue

        for marker in markers:
            msgstr_val = _extract_po_string(entry, marker)
            if msgstr_val is None:
                continue
            # English locale may leave msgstr empty (identity translation).
            # Other locales: empty msgstr means translation missing — still
            # check, because an empty string has zero placeholders while the
            # msgid may have some (a real bug).
            if msgstr_val == "" and locale == "en":
                continue
            str_vars = set(_PLACEHOLDER_RE.findall(msgstr_val))
            if id_vars != str_vars:
                pytest.fail(
                    f"{po_path.relative_to(BASE)}: placeholder mismatch in entry #{i}\n"
                    f"  marker: {marker}\n"
                    f"  msgid: {msgid!r}\n"
                    f"  msgid placeholders: {sorted(id_vars)}\n"
                    f"  msgstr: {msgstr_val!r}\n"
                    f"  msgstr placeholders: {sorted(str_vars)}"
                )


# ── helpers ──────────────────────────────────────────────────────────────────


def _split_entries(content: str) -> list[str]:
    """Split a PO file into individual translation entries."""
    return re.split(r"\n\n(?!\s*#~)", content)


def _extract_po_string(text: str, marker: str) -> str | None:
    """Extract the concatenated quoted-string value for *marker* from a PO entry.

    Handles both single-line::

        msgid "foo %(bar)s"

    And multi-line::

        msgid ""
        "foo %(bar)s"
        "baz"
    """
    lines = text.split("\n")
    parts: list[str] = []
    collecting = False
    prefix = marker + " "
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            # ``marker "content"`` or ``marker ""`` (multi-line start)
            quote_start = stripped.index('"')
            inner = stripped[quote_start + 1 :]
            if inner.endswith('"'):
                inner = inner[:-1]
            parts.append(inner)
            collecting = True
        elif collecting and stripped.startswith('"') and stripped.endswith('"'):
            # Continuation ``"text"`` line
            parts.append(stripped[1:-1])
        elif collecting:
            break
    return "".join(parts) if parts else None
