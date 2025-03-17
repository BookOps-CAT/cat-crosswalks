from datetime import datetime

import pytest

from src.lpa_reclass_utils import (
    change_item_varFields,
    construct_item_internal_note,
    construct_subfields_for_lcc,
    get_callnumber,
    get_item_nos_from_bib_response,
    has_special_cutter,
    is_callnumber_field,
    normalize_callnumber,
)


def test_change_item_varFields_no_existing_callnumber():
    item = {
        "id": "12345678",
        "varFields": [{"fieldTag": "b", "content": "33433006540185"}],
    }
    new_callnumber_field = {
        "fieldTag": "c",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": [{"tag": "a", "content": "FOO"}, {"tag": "i", "content": "BAR"}],
    }
    res = change_item_varFields(item=item, callnumber_field=new_callnumber_field)
    new_fields = item["varFields"]
    internal_note = {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: MISSING on item)",
    }
    new_fields.append(new_callnumber_field)
    new_fields.append(internal_note)
    assert res == new_fields


def test_change_item_varFields_with_existing_callnumber():
    old_callnumber = "SPAM"
    item = {
        "id": "12345678",
        "varFields": [
            {"fieldTag": "b", "content": "33433006540185"},
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"tag": "h", "content": old_callnumber}],
            },
        ],
    }
    new_callnumber_field = {
        "fieldTag": "c",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": [{"tag": "h", "content": "FOO"}, {"tag": "i", "content": "BAR"}],
    }
    res = change_item_varFields(item=item, callnumber_field=new_callnumber_field)
    new_fields = item["varFields"]
    internal_note = {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: {old_callnumber})",
    }
    new_fields.append(new_callnumber_field)
    new_fields.append(internal_note)
    assert res == new_fields


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
def test_get_callnumber(arg, expectation):
    assert get_callnumber(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [("yes", True), (" Yes ", True), ("", False), (" ", False), ("foo", False)],
)
def test_has_special_cutter(arg, expectation):
    assert has_special_cutter(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ({"26": {"label": "LOCATION", "value": "multi"}}, False),
        (
            {
                "fieldTag": "a",
                "marcTag": "100",
                "ind1": "1",
                "ind2": " ",
                "subfields": [],
            },
            False,
        ),
        (
            {
                "fieldTag": "c",
                "marcTag": "245",
                "ind1": "1",
                "ind2": "0",
                "subfields": [],
            },
            False,
        ),
        (
            {
                "fieldTag": "y",
                "marcTag": "852",
                "ind1": "1",
                "ind2": "0",
                "subfields": [],
            },
            False,
        ),
        (
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [],
            },
            True,
        ),
        (
            {
                "fieldTag": "q",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [],
            },
            True,
        ),
    ],
)
def is_callnumber_field(arg, expectation):
    assert is_callnumber_field(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (' *FOO bar .,()"baz +" ', "*FOO bar baz +"),
        (" *ZP-*PYO+ n.c. 2, no. 7 ", "*ZP*PYO+ nc 2 no 7"),
    ],
)
def test_normalize_callnumer(arg, expectation):
    assert normalize_callnumber(arg) == expectation


def test_temp():
    from src.lpa_reclass_utils import connect2sierra, get_items

    sid = "32153977"
    conn = connect2sierra()
    res = get_items(sid, conn)
    # print(res)


def test_construct_item_internal_note():
    # print(construct_item_internal_note("Foo"))
    pass
