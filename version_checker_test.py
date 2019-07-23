from version_checker import is_versioned_tag


def test_versioned_tag_tester_accepts_correct_tags():
    assert is_versioned_tag("1.2")