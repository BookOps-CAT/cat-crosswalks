import pytest

from src.loa_reclass import (
    construct_callno_field,
    is_valid_item,
    select_050_field,
    get_lcc_subfields_from_bib,
)


def test_construct_callno_field():
    field_tag = "c"
    subfields = [{"tag": "h", "content": "FOO"}, {"tag": "i", "content": "BAR"}]
    assert construct_callno_field(subfields, field_tag) == {
        "fieldTag": field_tag,
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": subfields,
    }


def test_is_valid_item_success(stub_loa_item):
    assert is_valid_item(stub_loa_item) is True


def test_is_valid_item_wrong_location(stub_loa_item):
    stub_loa_item["location"]["code"] = "foo"
    assert is_valid_item(stub_loa_item) is False


def test_is_valid_item_different_callno(stub_loa_item):
    stub_loa_item["varFields"][1]["subfields"][0]["content"] = "foo"
    assert is_valid_item(stub_loa_item) is False


def test_select_050_field_lc(stub_bib_as_json):
    assert select_050_field(stub_bib_as_json) == {
        "fieldTag": "y",
        "marcTag": "050",
        "ind1": "0",
        "ind2": "0",
        "subfields": [
            {"tag": "a", "content": "BAZ"},
            {"tag": "b", "content": "QUX"},
        ],
    }


def test_select_050_field_non_lc(stub_bib_as_json):
    stub_bib_as_json["varFields"][1]["ind2"] = "4"
    assert select_050_field(stub_bib_as_json) == {
        "fieldTag": "y",
        "marcTag": "050",
        "ind1": " ",
        "ind2": "4",
        "subfields": [
            {"tag": "a", "content": "FOO"},
            {"tag": "b", "content": "BAR"},
        ],
    }


def test_select_050_field_no_050(stub_bib_as_json):
    del stub_bib_as_json["varFields"][0:2]
    assert select_050_field(stub_bib_as_json) == {}


def test_get_lcc_subfields_from_bib(stub_bib_as_json):
    assert get_lcc_subfields_from_bib(stub_bib_as_json) == [
        {"tag": "h", "content": "BAZ"},
        {"tag": "i", "content": "QUX"},
    ]
