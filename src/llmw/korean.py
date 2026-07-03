"""Rule-based Korean particle (조사) stripping for search query terms.

Deliberately not a full morphological analyzer: `llmw` is a lightweight,
model-free CLI, and a real analyzer (e.g. `kiwipiepy`) needs a ~35 MB model
package. This only strips a trailing particle from an all-Hangul token so a
particle-suffixed query term ("스탯창을") also matches the bare noun
("스탯창") that FTS5 has indexed — prefix matching is otherwise asymmetric:
a query token can only prefix-match an indexed token at least as long as
itself, so a longer, particle-suffixed query term misses a shorter indexed
noun.
"""

from __future__ import annotations

import re

_HANGUL_TOKEN_RE = re.compile(r"^[가-힣]+$")

# Sorted longest-first below so a compound particle (e.g. "으로부터")
# strips whole before a shorter suffix-overlapping particle ("로", "으로")
# would otherwise match part of it.
_JOSA_RAW = (
    "으로부터", "에서부터",
    "이라는", "에게서", "한테서",
    "께서", "에서", "에게", "한테", "라는", "처럼", "보다", "부터",
    "까지", "조차", "마저", "밖에", "대로", "이나", "이란", "으로",
    "로서", "로써", "마다",
    "은", "는", "이", "가", "을", "를", "에", "의", "도", "만",
    "와", "과", "로", "나", "란",
)
_JOSA: tuple[str, ...] = tuple(sorted(_JOSA_RAW, key=len, reverse=True))
_JOSA_SET: frozenset[str] = frozenset(_JOSA_RAW)


def strip_josa(token: str) -> str | None:
    """Return the stem with a trailing particle removed, or ``None`` if no
    particle applies — the token is not all-Hangul, is too short, or the
    token itself IS a particle (stripping it would leave nothing, or would
    incorrectly peel a shorter particle off a longer particle that merely
    happens to end with it, e.g. "으로" ending with "로")."""
    if len(token) < 2 or not _HANGUL_TOKEN_RE.match(token):
        return None
    if token in _JOSA_SET:
        return None
    for josa in _JOSA:
        if len(token) > len(josa) and token.endswith(josa):
            return token[: -len(josa)]
    return None
