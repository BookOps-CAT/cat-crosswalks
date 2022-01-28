from pymarc import Field

from src.flourish_bibs import (
    add_command_tag,
    create_item_tag,
    flip_911,
    get_call_no,
    processed_file_path,
)


def test_processed_file_path():
    assert processed_file_path("C:/foo/bar/spam.mrc") == "C:/foo/bar\\spam-PRC.mrc"


def test_flip_911(stub_bib):
    stub_bib.add_field(Field(tag="911", indicators=[" ", " "], subfields=["a", "RL"]))

    flip_911(stub_bib)

    assert stub_bib.get_fields("911") == []
    assert str(stub_bib["910"]) == "=910  \\\\$aRL"


def test_flip_910_correctly_coded(stub_bib):
    stub_bib.add_field(Field(tag="910", indicators=[" ", " "], subfields=["a", "RL"]))

    tags = stub_bib.get_fields("910")
    assert len(tags) == 1
    assert str(tags[0]) == "=910  \\\\$aRL"


def test_get_call_no_success(stub_bib):
    stub_bib.add_field(Field(tag="852", indicators=["8", " "], subfields=["h", "foo"]))

    assert get_call_no(stub_bib) == "foo"


def test_get_call_no_missing_tag(stub_bib, capfd):
    get_call_no(stub_bib)
    captured = capfd.readouterr()

    assert "Bib # 123 is missing correct 852 tag" in captured.out


def test_get_call_no_invalid_indicator(stub_bib, capfd):
    stub_bib.add_field(Field(tag="852", indicators=[" ", " "], subfields=["h", "foo"]))
    get_call_no(stub_bib)
    captured = capfd.readouterr()

    assert "Bib # 123 is missing correct 852 tag" in captured.out


def test_get_call_no_invalid_subfield(stub_bib, capfd):
    stub_bib.add_field(Field(tag="852", indicators=[" ", "8"], subfields=["a", "foo"]))
    get_call_no(stub_bib)
    captured = capfd.readouterr()

    assert "Bib # 123 is missing correct 852 tag" in captured.out


def test_add_command_tag(stub_bib):
    add_command_tag(stub_bib)

    tags = stub_bib.get_fields("949")
    assert len(tags) == 1
    assert str(stub_bib["949"]) == "=949  \\\\$a*b2=c;recs=oclcgw;"


def test_create_item_tag(stub_bib):
    stub_bib.add_field(Field(tag="852", indicators=["8", " "], subfields=["h", "foo"]))

    create_item_tag(stub_bib, "foo")

    tags = stub_bib.get_fields("949")
    assert len(tags) == 1
    assert (
        str(tags[0])
        == "=949  \\1$z8528$afoo$iBARCODE TO BE SUPPLIED$lmym38$t7$h32$o1$s-$vMUS/"
    )
