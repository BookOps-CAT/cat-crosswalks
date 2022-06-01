from src.song_index import (
    get_oclc_no,
    get_lccn,
    get_isbns,
    get_standard_nos,
    get_publisher_nos,
)

from pymarc import Field
import pytest


@pytest.mark.parametrize(
    "control_no,code,expectation",
    [
        ("1234", "OCoLC", "1234"),
        ("1234", "NYP", None),
        ("ocm1234", "OCoLC", "1234"),
        ("odn1234", "OCoLC", None),
    ],
)
def test_get_oclc_num_001_tag(control_no, code, expectation, stub_bib):
    stub_bib["001"].data = control_no
    stub_bib.add_field(Field(tag="003", data=code))

    assert get_oclc_no(stub_bib) == expectation


@pytest.mark.parametrize(
    "fields,expectation",
    [
        (["(WaOLN)nyp1945979"], None),
        (["(NN-PD)877017383", "(WaOLN)Y080000045"], None),
        (["(WaOLN)nyp1945979", "(OCoLC)1234"], "1234"),
    ],
)
def test_get_oclc_num_035_tag(stub_bib, fields, expectation):
    stub_bib.remove_fields("001")
    for f in fields:
        stub_bib.add_field(Field(tag="035", subfields=["a", f]))

    assert get_oclc_no(stub_bib) == expectation


@pytest.mark.parametrize("arg,expectation", [("1234", "1234"), ("nyp1234", None)])
def test_get_oclc_num_991_tag(stub_bib, arg, expectation):
    stub_bib.remove_fields("001")
    stub_bib.add_field(Field(tag="991", subfields=["y", arg]))

    assert get_oclc_no(stub_bib) == expectation


@pytest.mark.parametrize(
    "arg,expectation", [("   68021203", "68021203"), (" 12345", "12345")]
)
def test_get_lccn(stub_bib, arg, expectation):
    stub_bib.add_field(Field(tag="010", subfields=["a", arg]))

    assert get_lccn(stub_bib) == expectation


def test_get_lccn_missing(stub_bib):
    assert get_lccn(stub_bib) is None


def test_get_lccn_missing_sub(stub_bib):
    stub_bib.add_field(Field(tag="010", subfields=["b", "1234"]))

    assert get_lccn(stub_bib) is None


@pytest.mark.parametrize(
    "subs,expectation",
    [
        (["z", "12345"], []),
        (["a", "12345 (pbk.)"], ["12345"]),
        (["a", "12345x"], ["12345x"]),
    ],
)
def test_get_isbns(stub_bib, subs, expectation):
    stub_bib.add_field(Field(tag="020", subfields=subs))

    assert get_isbns(stub_bib) == expectation


def test_get_isbns_missing(stub_bib):
    stub_bib.remove_fields("020")

    assert get_isbns(stub_bib) == []


def test_get_standard_nos_missing(stub_bib):
    stub_bib.remove_fields("024")

    assert get_standard_nos(stub_bib) == []


@pytest.mark.parametrize(
    "arg,expectation",
    [(["a", "1234"], ["1234"]), (["z", "1234"], []), (["a", "  1234  "], ["1234"])],
)
def test_get_standard_nos(stub_bib, arg, expectation):
    stub_bib.add_field(Field(tag="024", subfields=arg))

    assert get_standard_nos(stub_bib) == expectation


def test_get_publisher_nos_missing(stub_bib):
    stub_bib.remove_fields("028")

    assert get_publisher_nos(stub_bib) == []


@pytest.mark.parametrize(
    "arg,expectation",
    [(["a", "1234"], ["1234"]), (["z", "1234"], []), (["a", "  1234  "], ["1234"])],
)
def test_get_publisher_nos(stub_bib, arg, expectation):
    stub_bib.add_field(Field(tag="028", subfields=arg))

    assert get_publisher_nos(stub_bib) == expectation
