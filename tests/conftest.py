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


@pytest.fixture
def stub_bib_as_json():
    return {
        "id": 1000001,
        "updatedDate": "2009-07-06T15:30:13Z",
        "createdDate": "2003-05-08T15:55:00Z",
        "deleted": False,
        "suppressed": False,
        "available": True,
        "lang": {"code": "eng", "name": "English"},
        "title": "Hey, what's wrong with this one?",
        "author": "Wojciechowska, Maia, 1927-",
        "materialType": {"code": "a", "value": "Book"},
        "bibLevel": {"code": "m", "value": "MONOGRAPH"},
        "publishYear": 1969,
        "catalogDate": "1990-10-10",
        "country": {"code": "nyu", "name": "New York (State)"},
        "normTitle": "hey whats wrong with this one",
        "normAuthor": "wojciechowska maia 1927",
        "locations": [
            {"code": "a", "name": "SJSU"},
        ],
        "varFields": [
            {
                "fieldTag": "a",
                "marcTag": "100",
                "ind1": "1",
                "ind2": " ",
                "subfields": [
                    {"tag": "a", "content": "Wojciechowska, Maia,"},
                    {"tag": "d", "content": "1927-"},
                ],
            },
            {
                "fieldTag": "b",
                "marcTag": "700",
                "ind1": "1",
                "ind2": " ",
                "subfields": [{"tag": "a", "content": "Sandin, Joan."}],
            },
            {
                "fieldTag": "d",
                "marcTag": "650",
                "ind1": " ",
                "ind2": "0",
                "subfields": [
                    {"tag": "a", "content": "Families"},
                    {"tag": "v", "content": "Fiction."},
                ],
            },
            {
                "fieldTag": "o",
                "marcTag": "001",
                "ind1": " ",
                "ind2": " ",
                "content": "170",
            },
            {
                "fieldTag": "p",
                "marcTag": "260",
                "ind1": " ",
                "ind2": " ",
                "subfields": [
                    {"tag": "a", "content": "New York,"},
                    {"tag": "b", "content": "Harper & Row"},
                    {"tag": "c", "content": "[1969]"},
                ],
            },
            {
                "fieldTag": "t",
                "marcTag": "245",
                "ind1": "1",
                "ind2": "0",
                "subfields": [
                    {"tag": "a", "content": "Hey, what's wrong with this one?"},
                    {"tag": "c", "content": "Pictures by Joan Sandin."},
                ],
            },
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [
                    {"tag": "h", "content": "FOO, BAR"},
                    {"tag": "m", "content": "SPAM"},
                ],
            },
            {
                "fieldTag": "q",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [
                    {"tag": "a", "content": "BAZ."},
                    {"tag": "z", "content": "QUX"},
                ],
            },
            {
                "fieldTag": "y",
                "marcTag": "008",
                "ind1": " ",
                "ind2": " ",
                "content": "690505s1969    nyua   j      000 1 eng  cam   ",
            },
            {"fieldTag": "_", "content": "00000cam  2200000   4500"},
        ],
    }


@pytest.fixture
def stub_lpa_item():
    return {
        "id": "3159578",
        "callNumber": "FOO, BAR",
        "barcode": "33433030947877",
        "location": {"code": "pam11", "name": "LPA REF"},
        "fixedFields": [
            {
                "label": "LOCATION",
                "number": 79,
                "value": "pam11",
                "display": "Performing Arts Research Collections - Music - Reference",
            },
        ],
        "varFields": [
            {"fieldTag": "b", "content": "33433030947877"},
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"tag": "h", "content": "FOO, BAR"}],
            },
        ],
    }


@pytest.fixture
def stub_other_item():
    return {
        "id": "3159579",
        "callNumber": "BAZ",
        "barcode": "33433064168457",
        "location": {"code": "rcmb8", "name": "OFF SITE"},
        "fixedFields": [
            {
                "label": "LOCATION",
                "number": 79,
                "value": "rcmb8",
                "display": "OFF SITE",
            },
        ],
        "varFields": [
            {"fieldTag": "b", "content": "33433064168457"},
            {
                "fieldTag": "c",
                "marcTag": "852",
                "ind1": "8",
                "ind2": " ",
                "subfields": [{"tag": "h", "content": "BAZ"}],
            },
        ],
    }
