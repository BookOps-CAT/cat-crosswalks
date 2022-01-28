from pymarc import Record, Field

import pytest


@pytest.fixture
def stub_bib():
    bib = Record()
    bib.leader = "02866pam  2200517 i 4500"
    bib.add_field(Field(tag="008", data="190306s2017    ht a   j      000 1 hat d"))
    bib.add_field(Field(tag="001", data="123"))
    bib.add_field(
        Field(
            tag="100",
            indicators=["1", " "],
            subfields=["a", "Adams, John,", "e", "author."],
        )
    )
    bib.add_field(
        Field(
            tag="245",
            indicators=["1", "4"],
            subfields=["a", "The foo /", "c", "by John Adams."],
        )
    )
    bib.add_field(
        Field(
            tag="264",
            indicators=[" ", "1"],
            subfields=["a", "Bar :", "b", "New York,", "c", "2021"],
        )
    )

    return bib
