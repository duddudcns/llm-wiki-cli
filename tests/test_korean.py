from llmw.korean import strip_josa


def test_strip_josa_object_particle():
    assert strip_josa("스탯창을") == "스탯창"


def test_strip_josa_locative_particle():
    assert strip_josa("포탈에서") == "포탈"


def test_strip_josa_compound_particle_strips_whole_suffix():
    assert strip_josa("맵으로부터") == "맵"


def test_strip_josa_longest_suffix_wins():
    # "위에서" must strip the 2-char "에서", not stop at a shorter overlap.
    assert strip_josa("위에서") == "위"


def test_strip_josa_returns_none_for_bare_word():
    assert strip_josa("포탈") is None
    assert strip_josa("방식") is None


def test_strip_josa_never_empties_token():
    # The token IS a particle; stripping it would leave an empty stem.
    assert strip_josa("에서") is None
    assert strip_josa("으로") is None


def test_strip_josa_skips_short_tokens():
    assert strip_josa("은") is None
    assert strip_josa("가") is None


def test_strip_josa_skips_mixed_script_tokens():
    assert strip_josa("스탯창UI") is None
    assert strip_josa("context") is None
    assert strip_josa("123") is None


def test_strip_josa_false_strip_is_recall_safe_and_documented():
    # "도로" (road) happens to end in the particle "로" — this rule-based
    # stripper has no way to know it's not a particle here. It's stripped
    # to "도" anyway: recall-safe by construction (the stem is always a
    # prefix of the original word, so "도로*" still matches "도로"), just
    # ranking noise. Pinned intentionally, not a bug.
    assert strip_josa("도로") == "도"
