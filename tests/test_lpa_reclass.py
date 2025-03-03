import pytest

from src.lpa_reclass import construct_subfields_for_lcc, get_item_nos_from_bib_response


@pytest.mark.parametrize(
    "arg1,arg2,expectation",
    [
        (
            "ML100.G13 2019",
            False,
            [dict(tag="h", content="ML100"), dict(tag="i", content=".G13 2019")],
        ),
        (
            "ML101.G7 S64 1984",
            True,
            [dict(tag="h", content="ML101.G7"), dict(tag="i", content="S64 1984")],
        ),
    ],
)
def test_construct_subfields_for_lcc(arg1, arg2, expectation):
    assert construct_subfields_for_lcc(arg1, arg2) == expectation


def test_get_item_nos_from_bib_response():
    assert get_item_nos_from_bib_response(
        ["https://nypl-sierra-test.iii.com/iii/sierra-api/v6/items/14381985"]
    ) == ["14381985"]
