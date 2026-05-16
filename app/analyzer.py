"""Pure text-analysis logic.

This module has *no* Flask import on purpose. The analyzer is a domain
function: given a string, return statistics. Keeping it framework-free
means it can be:
  * unit-tested in isolation (no test client, no app context);
  * reused from a CLI script, a background worker, or another service;
  * benchmarked without HTTP overhead.

We deliberately do NOT wrap this in a class or strategy hierarchy.
There is one algorithm and one return shape today. Introducing
abstraction "for the future" would be speculative generality — easy to
add later when a second analyzer actually exists.
"""

import re
from collections import Counter
from functools import lru_cache

# Regex objects are pre-compiled at import time. `re.compile` is
# non-trivial (parses the pattern, builds a state machine); doing it
# once at module load avoids re-doing it on every request. The cost is
# paid before the first request ever lands.
_WORD_RE = re.compile(r"\b[\w']+\b")
_SENTENCE_RE = re.compile(r"[.!?]+")
_WHITESPACE_RE = re.compile(r"\s+")

# `frozenset` for O(1) membership tests and to signal "this set is a
# constant — do not mutate." A 5-element frozenset beats a string
# `in "aeiou"` for repeated lookups inside the hot loop.
_VOWELS = frozenset("aeiou")


@lru_cache(maxsize=128)
def analyze(text: str) -> dict:
    """Return a dict of statistics for `text`.

    Memoized with a bounded LRU cache because the realistic usage
    pattern (a user typing, pausing, deleting, re-typing the same
    paragraph) produces many repeat inputs. Cache hits skip the entire
    computation. The cache is bounded so memory cannot grow without
    limit; `maxsize=128` is small enough to be irrelevant on any
    server and large enough to absorb a typical editing session.

    Returned dict keys are stable — the view layer and the frontend
    both depend on this exact shape, so changes here are a contract
    break.
    """
    # Single linear pass over the text classifies every character at
    # once. Doing this in one loop instead of three separate passes
    # (one per category) keeps the work O(n) with a small constant.
    num_vowels = 0
    num_consonants = 0
    letters: list[str] = []

    for ch in text:
        lower = ch.lower()
        if lower.isalpha():
            letters.append(lower)
            if lower in _VOWELS:
                num_vowels += 1
            else:
                num_consonants += 1

    # Word and sentence segmentation use the pre-compiled regexes.
    # `findall` returns a list (we need its length and per-word
    # length); `split` is consumed lazily via a generator expression
    # to avoid materializing an intermediate list we never keep.
    words = _WORD_RE.findall(text)
    word_count = len(words)
    sentence_count = sum(1 for s in _SENTENCE_RE.split(text) if s.strip())

    return {
        "vowels": num_vowels,
        "consonants": num_consonants,
        "characters": len(text),
        "characters_no_spaces": len(_WHITESPACE_RE.sub("", text)),
        "words": word_count,
        "sentences": sentence_count,
        # Guarded division — `or 0` would coerce a legitimate 0.0
        # into the same value, but here we want exactly 0 when there
        # are no words to avoid a ZeroDivisionError.
        "avg_word_length": (
            round(sum(len(w) for w in words) / word_count, 1)
            if word_count
            else 0
        ),
        # Counter.most_common(1) is O(n) for small k; faster than
        # sorting the full distribution when we only need the top one.
        "most_common_letter": (
            Counter(letters).most_common(1)[0][0].upper() if letters else "—"
        ),
    }
