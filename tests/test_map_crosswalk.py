import pytest


from src.maps_crosswalk import (
    construct_geo_subject_subfields,
    determine_control_number_sequence,
    encode_scale,
    has_true_hyphen,
    norm_scale_text,
    norm_pub_date_text,
    norm_subfield_separator,
    encode_pub_date,
    split_subject_elements,
)


@pytest.mark.parametrize("arg,expectation", [(1, "00000001"), (123, "00000123")])
def test_determine_control_number_sequence(arg, expectation):
    assert determine_control_number_sequence(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("1:800,000", "800000"),
        ("1:500", "500"),
        ("N.S", None),
        ("Scales Vary", None),
        ("foo", None),
    ],
)
def test_encode_scale(arg, expectation):
    assert encode_scale(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("1:500", "Scale 1:500"),
        ("N.S", "Scale not given"),
        (None, "Scale not given"),
        ("", "Scale not given"),
    ],
)
def test_norm_scale_text(arg, expectation):
    assert norm_scale_text(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (None, "    "),
        ("", "    "),
        ("2015", "2015"),
        ("[1880]", "1880"),
        ("[19--]", "19uu"),
        ("[186-]", "186u"),
    ],
)
def test_norm_pub_date(arg, expectation):
    assert encode_pub_date(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (None, "[date of publication not identified]"),
        ("", "[date of publication not identified]"),
        ("1880", "1880"),
        ("[19--]", "[19--]"),
    ],
)
def test_norm_pub_date_text(arg, expectation):
    assert norm_pub_date_text(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("Minnesota - Maps", ["a", "Minnesota", "v", "Maps."]),
        ("Minnesota -- Maps", ["a", "Minnesota", "v", "Maps."]),
        ("Minnesota-Maps", ["a", "Minnesota", "v", "Maps."]),
        ("Minnesota--Maps", ["a", "Minnesota", "v", "Maps."]),
        ("Chicago (Ill.) - Guidebooks", ["a", "Chicago (Ill.)", "v", "Guidebooks."]),
        (
            "Klondike River Valley (Yukon) - Gold discoveries - Maps.",
            [
                "a",
                "Klondike River Valley (Yukon)",
                "x",
                "Gold discoveries",
                "v",
                "Maps.",
            ],
        ),
        ("United States", ["a", "United States."]),
        ("United States - Maps", ["a", "United States", "v", "Maps."]),
        (
            "United States -- History -- Civil War, 1861-1865 -- Maps.",
            [
                "a",
                "United States",
                "x",
                "History",
                "y",
                "Civil War, 1861-1865",
                "v",
                "Maps.",
            ],
        ),
    ],
)
def test_construct_geo_subject_subfields(arg, expectation):
    assert construct_geo_subject_subfields(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo-bar", True),
        ("foo - bar", False),
        ("foo -bar", False),
        ("foo- bar", False),
        ("foo--bar", False),
        ("foo.-bar", True),
    ],
)
def test_has_true_hyphen(arg, expectation):
    assert has_true_hyphen(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo - bar", "foo -- bar"),
        ("foo -- bar", "foo -- bar"),
        ("foo -bar", "foo --bar"),
        ("foo- bar", "foo-- bar"),
        ("foo-bar", "foo--bar"),
    ],
)
def test_norm_subfield_separator(arg, expectation):
    assert norm_subfield_separator(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo - bar - spam", ["foo", "bar", "spam"]),
        (" foo -- bar -- spam ", ["foo", "bar", "spam"]),
    ],
)
def test_split_subject_elements(arg, expectation):
    assert split_subject_elements(arg) == expectation
