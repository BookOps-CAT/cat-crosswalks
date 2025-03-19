from datetime import datetime

import pytest

from src.lpa_reclass_utils import (
    MultiCallNumError,
    change_item_varFields,
    construct_item_internal_note,
    construct_subfields_for_lcc,
    determine_safe_to_delete_item_callnumbers,
    get_bib_callnumber,
    get_callnumber,
    get_item_nos_from_bib_response,
    get_other_item_callnumbers,
    has_special_cutter,
    is_callnumber_field,
    is_lpa_ref_location,
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
    new_fields = item["varFields"][:1]  # remove old callnumber
    internal_note = {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: {old_callnumber})",
    }
    new_fields.append(new_callnumber_field)
    new_fields.append(internal_note)
    assert res == new_fields


def test_change_item_varFields_without_any_varFields():
    item = {
        "id": "12345678",
        "varFields": [],
    }
    new_callnumber_field = {
        "fieldTag": "c",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": [{"tag": "h", "content": "FOO"}, {"tag": "i", "content": "BAR"}],
    }
    res = change_item_varFields(item=item, callnumber_field=new_callnumber_field)
    new_fields = []
    internal_note = {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: MISSING on item)",
    }
    new_fields.append(new_callnumber_field)
    new_fields.append(internal_note)
    assert res == new_fields


def test_change_item_varFields_with_multiple_callnumber_fields():
    old_callnumber1 = "SPAM1"
    old_callnumber2 = "SPAM2"
    item = {
        "id": "12345678",
        "varFields": [
            {"fieldTag": "b", "content": "33433006540185"},
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"tag": "h", "content": old_callnumber1}],
            },
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"tag": "h", "content": old_callnumber2}],
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

    with pytest.raises(MultiCallNumError):
        change_item_varFields(item=item, callnumber_field=new_callnumber_field)


def test_construct_item_internal_note():
    old_callnumber = "FOO"
    assert construct_item_internal_note(olc_callnumber) == {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: {old_callnumber})",
    }


def construct_lcc_field():
    field_tag = "c"
    subfields = [{"tag": "h", "content": "FOO"}, {"tag": "i", "content": "BAR"}]
    assert construct_lcc_field(subfields, field_tag) == {
        "fieldTag": fieldTag,
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": subfields,
    }


@pytest.mark.parametrize(
    "arg1,arg2",
    [
        (None, "a"),
        ("foo", "a"),
        ([{"tag": "h", "content": "FOO"}], None),
        ([{"tag": "h", "content": "FOO"}], []),
    ],
)
def construct_lcc_field_exceptions(arg1, arg2):
    with pytest.raises(TypeError):
        construct_lcc_field(subfields=arg1, fieldTag=arg2)


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


def test_determine_safe_to_detete_item_callnumbers():
    pass


def test_get_bibcallnumber(stub_bib_as_json):
    assert get_bib_callnumber(stub_bib_as_json) == {"FOO BAR SPAM", "BAZ QUX"}


def test_get_item_nos_from_bib_response():
    assert get_item_nos_from_bib_response(
        ["https://nypl-sierra-test.iii.com/iii/sierra-api/v6/items/14381985"]
    ) == ["14381985"]


def test_get_other_item_callnumbers_not_present(stub_item):
    items = [stub_item]
    assert get_other_item_callnumbers(items) == {""}


def test_get_other_item_callnumbers_present(stub_item):
    second_item = stub_item.copy()
    second_item["barcode"] = ("33433064168457",)
    second_item["location"] = {"code": "rcmb8", "name": "OFF SITE"}
    second_item["fixedFields"] = [
        {
            "label": "LOCATION",
            "number": 79,
            "value": "rcmb8",
            "display": "OFF SITE",
        },
    ]
    second_item["varFields"] = [
        {"fieldTag": "b", "content": "33433064168457"},
        {
            "fieldTag": "c",
            "marcTag": "852",
            "ind1": "8",
            "ind2": " ",
            "content": [{"tag": "h", "content": "BAZ"}],
        },
    ]
    items = [stub_item, second_item]
    assert get_other_item_callnumbers(items) == {"BAZ"}


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
def test_is_callnumber_field(arg, expectation):
    assert is_callnumber_field(arg) == expectation


@pytest.mark.parametrize(
    "fixture_name,expectation",
    [
        ("stub_lpa_item", True),
        ("stub_other_item", False),
    ],
)
def test_is_lpa_ref_location(request, fixture_name, expectation):
    arg = request.getfixturevalue(fixture_name)
    assert is_lpa_ref_location(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (' *FOO bar .,()"baz +" ', "*FOO bar baz +"),
        (" *ZP-*PYO+ n.c. 2, no. 7 ", "*ZP*PYO+ nc 2 no 7"),
    ],
)
def test_normalize_callnumer(arg, expectation):
    assert normalize_callnumber(arg) == expectation


# def test_temp():
#     from src.lpa_reclass_utils import connect2sierra, get_items

#     sid = "32153977"
#     conn = connect2sierra()
#     res = get_items(sid, conn)
# print(res)


def test_construct_item_internal_note():
    # print(construct_item_internal_note("Foo"))
    pass
