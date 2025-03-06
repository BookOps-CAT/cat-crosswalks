import pytest

from src.lpa_reclass_utils import (
    construct_subfields_for_lcc,
    get_subfield_contents,
    get_item_nos_from_bib_response,
    normalize_callnumber,
)


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


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ({"subfields": []}, ""),
        ({"subfields": [{"tag": "a", "content": "foo"}]}, "foo"),
        (
            {
                "subfields": [
                    {"tag": "a", "content": "foo"},
                    {"tag": "b", "content": "bar"},
                ]
            },
            "foo bar",
        ),
    ],
)
def test_get_subfield_contents(arg, expectation):
    assert get_subfield_contents(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (' *FOO bar .,()"baz +" ', "*FOO bar baz +"),
        (" *ZP-*PYO+ n.c. 2, no. 7 ", "*ZP*PYO+ nc 2 no 7"),
    ],
)
def test_normalize_callnumer(arg, expectation):
    assert normalize_callnumber(arg) == expectation
