"""
core/text_utils.py
------------------
Pure text-processing helpers: character-script detection, Hebrew/Latin boundary
spacing, GT punctuation normalization, and tokenization.

No filesystem access, no I/O, no side effects.
"""
from __future__ import annotations

import re
from typing import List


# ══════════════════════════════════════════════
# Script detection
# ══════════════════════════════════════════════

def _is_hebrew(ch: str) -> bool:
    return "֐" <= ch <= "׿" or "יִ" <= ch <= "ﭏ"


def _is_latin(ch: str) -> bool:
    return ch.isascii() and ch.isalpha()


def _needs_boundary_space(prev: str, cur: str) -> bool:
    """
    Return True if a space should be inserted between prev and cur.
    Handles Hebrew<->Latin and Hebrew<->digit boundaries.

        Hebrew + Latin  : "בTone"   -> "ב Tone"
        Latin  + Hebrew : "Toneכדי" -> "Tone כדי"
        Hebrew + digit  : "ל25"     -> "ל 25"
        digit  + Hebrew : "25ב"     -> "25 ב"
    """
    prev_heb = _is_hebrew(prev)
    prev_lat = _is_latin(prev)
    prev_dig = prev.isdigit()
    cur_heb  = _is_hebrew(cur)
    cur_lat  = _is_latin(cur)
    cur_dig  = cur.isdigit()

    return (
        (prev_heb and cur_lat) or
        (prev_lat and cur_heb) or
        (prev_heb and cur_dig) or
        (prev_dig and cur_heb)
    )


def insert_script_boundary_spaces(text: str) -> str:
    """
    Insert a space wherever adjacent characters cross a Hebrew/Latin/digit
    script boundary with no whitespace between them.

        "בTone"           ->  "ב Tone"
        "לClassifier"     ->  "ל Classifier"
        "קיבלהTrue"       ->  "קיבלה True"
        "ל25"             ->  "ל 25"
        "לאינטגרציהSAP"   ->  "לאינטגרציה SAP"
    """
    if not text:
        return text
    chars  = list(text)
    result = [chars[0]]
    for i in range(1, len(chars)):
        prev, cur = chars[i - 1], chars[i]
        if _needs_boundary_space(prev, cur):
            result.append(" ")
        result.append(cur)
    return "".join(result)


# ══════════════════════════════════════════════
# Text normalization
# ══════════════════════════════════════════════

def clean_text(text: str) -> str:
    """
    Normalize text so both GT and parser produce identical tokens:
      1. Insert spaces at Hebrew<->Latin and Hebrew<->digit script boundaries.
      2. Collapse all whitespace runs to a single space and strip edges.

    Applied to BOTH parser output and GT text before tokenization.
    Word-separator removal (hyphens, slashes, etc.) is GT-only; see
    normalize_gt_punctuation().
    """
    text = insert_script_boundary_spaces(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_gt_punctuation(text: str) -> str:
    """
    Normalize punctuation in Ground Truth text to its ideal format.
    Applied to GT only — represents the target output format.

    Rules
    -----
    1. Standard punctuation (.  ?  !  ,) and brackets:
       Remove any space between the preceding word and the mark/closing bracket.
       Remove any space immediately after an opening bracket.
    2. Dashes (-): remove spaces around '-' for compound words (letter-letter);
       bullet dashes and date ranges are left untouched.
    3. Slashes (/): remove spaces on either side between non-whitespace chars.
    4. Colons (:): remove space before ':' when preceded by a letter.
    """
    # ── Rule 1: Standard punctuation & brackets ──────────────────
    # Remove space(s) before . ? ! , ) ] }
    text = re.sub(r'[ \t]+([.?!,)\]}])', r'\1', text)
    # Remove space(s) after opening bracket ( [ {
    text = re.sub(r'([\[({])[ \t]+', r'\1', text)

    # ── Rule 2: Dashes ────────────────────────────────────────────
    text = re.sub(
        r'(?<=[A-Za-z֐-׿יִ-ﭏ])[ \t]*-[ \t]*'
        r'(?=[A-Za-z֐-׿יִ-ﭏ])',
        '-',
        text,
        flags=re.MULTILINE,
    )

    # ── Rule 3: Slashes ───────────────────────────────────────────
    text = re.sub(r'(?<=[^\s])[ \t]*/[ \t]*(?=[^\s])', '/', text, flags=re.MULTILINE)

    # ── Rule 4: Colons ────────────────────────────────────────────
    text = re.sub(
        r'(?<=[A-Za-z֐-׿יִ-ﭏ])[ \t]+:(?!/)',
        ':',
        text,
        flags=re.MULTILINE,
    )

    return text


# ══════════════════════════════════════════════
# Token helpers
# ══════════════════════════════════════════════

def _is_punct_token(word: str) -> bool:
    """True if word is non-empty and contains only non-alphanumeric characters."""
    return bool(word) and all(not c.isalnum() for c in word)


def tokenize(text: str) -> List[str]:
    """
    Split text into tokens by whitespace; drop empty strings.

    Does NOT strip punctuation — punctuation tokens are intentionally preserved
    so diagnostics can detect misplaced-punctuation patterns.

    Applied to both GT and parser output before comparison.
    """
    return [word for word in text.split() if word]
