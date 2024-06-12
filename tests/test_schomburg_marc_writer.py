import pytest

from src.marc_writer_fix import skip_char


@pytest.mark.parametrize("arg,expectation", [
        ("The foo", "4"),
        ("A bar", "2"),
        ("An baz", "3"),
        ("Foo", "0"),
        ("And spam", "0")
    ])
def test_skip_char(arg, expectation):
    assert skip_char(arg) == expectation
