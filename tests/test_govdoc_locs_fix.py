import pytest

from src.govdoc_locs_fix import cleanup_locs


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("mai", "mai"),
        ("ia", ""),
        ("iarch", ""),
        ("slr", ""),
        ("iaslr", ""),
        ("mai@ia", "mai"),
        ("ia@iarch@mal", "mal"),
        ("mal@ia@scf", "mal,scf"),
    ],
)
def test_cleanup_locs(arg, expectation):
    assert cleanup_locs(arg) == expectation
