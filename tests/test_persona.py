from fc27trader.social.persona import anti_slop_preflight


def test_anti_slop_rewrites_canned_social_copy():
    result = anti_slop_preflight("Let's dive in!!!\n\n### HUGE TAKE\n### ANOTHER\nFollow for more")
    assert "let's dive in" not in result.rewritten.lower()
    assert "follow for more" not in result.rewritten.lower()
    assert result.flags
