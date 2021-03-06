import pytest


from src.maps_crosswalk import (
    construct_subject_subfields,
    construct_personal_author_subfields,
    construct_corporate_author_subfields,
    determine_control_number_sequence,
    encode_pub_date,
    encode_scale,
    has_invalid_last_chr,
    has_true_hyphen,
    identify_t100_subfield_d_position,
    identify_t100_subfield_d,
    identify_t100_subfield_q_position,
    identify_t100_subfield_q,
    norm_last_subfield,
    norm_scale_text,
    norm_pub_date_text,
    norm_subfield_separator,
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
        ("Minnesota -Maps", ["a", "Minnesota", "v", "Maps."]),
        ("Minnesota--Maps", ["a", "Minnesota", "v", "Maps."]),
        ("New Hampshire --Maps", ["a", "New Hampshire", "v", "Maps."]),
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
        (
            "Mount Auburn Cemetery (Cambridge, Mass.) -- Maps",
            ["a", "Mount Auburn Cemetery (Cambridge, Mass.)", "v", "Maps."],
        ),
    ],
)
def test_construct_subject_subfields(arg, expectation):
    assert construct_subject_subfields(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo-bar", True),
        ("foo - bar", False),
        ("foo -bar", False),
        ("foo- bar", False),
        ("foo--bar", False),
        ("foo.-bar", True),
        ("foo bar", False),
    ],
)
def test_has_true_hyphen(arg, expectation):
    assert has_true_hyphen(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo - bar", "foo@ bar"),
        ("foo -- bar", "foo@ bar"),
        ("foo -bar", "foo@bar"),
        ("foo- bar", "foo@bar"),
        ("foo-bar", "foo-bar"),
        ("foo --bar", "foo@bar"),
        ("foo-- bar", "foo@bar"),
        ("foo--bar", "foo@bar"),
        ("foo -- bar -- spam", "foo@ bar@ spam"),
    ],
)
def test_norm_subfield_separator(arg, expectation):
    assert norm_subfield_separator(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo - bar - spam", ["foo", "bar", "spam"]),
        (" foo -- bar -- spam ", ["foo", "bar", "spam"]),
        ("foo bar", ["foo bar"]),
        ("foo 1939-1945", ["foo 1939-1945"]),
        ("United States", ["United States"]),
    ],
)
def test_split_subject_elements(arg, expectation):
    assert split_subject_elements(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo", False),
        ("foo.", True),
        ("foo;", True),
        ("foo ", True),
        ("foos", False),
        ("United States", False),
    ],
)
def test_has_invalid_last_chr(arg, expectation):
    assert has_invalid_last_chr(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [("foo", "foo."), ("foo.", "foo."), ("foo..", "foo."), ("foo ", "foo.")],
)
def test_norm_last_subfield(arg, expectation):
    assert norm_last_subfield(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo (bar spam)", (4, 14)),
        ("foo", None),
        ("foo (bar", None),
        ("foo bar)", None),
    ],
)
def test_identify_t100_subfield_q_position(arg, expectation):
    assert identify_t100_subfield_q_position(arg) == expectation


@pytest.mark.parametrize(
    "arg1,arg2,expectation",
    [
        ("foo (bar spam)", (4, 14), "(bar spam)"),
        ("foo", None, None),
        ("foo (bar", None, None),
        ("foo bar)", None, None),
    ],
)
def test_identify_t100_subfield_q(arg1, arg2, expectation):
    assert identify_t100_subfield_q(arg1, arg2) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("Hall, Sidney", None),
        ("Otley, J.W.", None),
        ("Wyld, James, 1812-1887", "1812-1887"),
        ("Cary, John, approximately 1754-1835", "approximately 1754-1835"),
        ("Bartholomew, J. G. (John George), 1860-1920", "1860-1920"),
    ],
)
def test_identify_t100_subfield_d(arg, expectation):
    assert identify_t100_subfield_d(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("Hall, Sidney", ["a", "Hall, Sidney,", "e", "cartographer."]),
        ("Otley, J.W.", ["a", "Otley, J.W.,", "e", "cartographer."]),
        (
            "Cary, John, approximately 1754-1835",
            ["a", "Cary, John,", "d", "approximately 1754-1835,", "e", "cartographer."],
        ),
        (
            "Bartholomew, J. G. (John George), 1860-1920",
            [
                "a",
                "Bartholomew, J. G.",
                "q",
                "(John George),",
                "d",
                "1860-1920,",
                "e",
                "cartographer.",
            ],
        ),
        (
            "Wyld, James, 1812-1887",
            ["a", "Wyld, James,", "d", "1812-1887,", "e", "cartographer."],
        ),
        (
            "Bartholomew, J. G. (John George)",
            ["a", "Bartholomew, J. G.", "q", "(John George),", "e", "cartographer."],
        ),
    ],
)
def test_construct_personal_author_subfields(arg, expectation):
    assert construct_personal_author_subfields(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (
            "Rand McNally and Company",
            ["a", "Rand McNally and Company,", "e", "cartographer."],
        ),
        ("A. Hoen & Co.", ["a", "A. Hoen & Co.,", "e", "cartographer."]),
    ],
)
def test_construct_corporate_author_subfields(arg, expectation):
    assert construct_personal_author_subfields(arg) == expectation
