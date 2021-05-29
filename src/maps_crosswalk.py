"""
Crosswalk between map csv data and MARC21
"""

from collections import namedtuple
import csv
from datetime import datetime, date
import re
import warnings

from pymarc import Record, Field


try:
    from .utils import save2marc
except ImportError:
    from utils import save2marc


class SuspiciousDataWarning(Warning):
    pass


MapData = namedtuple(
    "MapData",
    [
        "barcode",
        "t100",
        "t110",
        "t245",
        "t246",
        "t250",
        "t255",
        "t260",
        "t490",
        "t500",
        "t505",
        "t561",
        "t655",
        "t852",
    ],
)


def determine_control_number_sequence(n):
    return str(n).zfill(8)


def create_timestamp():
    ts = datetime.utcnow()
    return ts.strftime("%Y%m%d%H%M%S.0")


def encode_scale(scale):
    if ":" in scale:
        idx = scale.index(":")
        return scale[idx + 1 :].replace(",", "")
    else:
        return None


def norm_scale_text(scale):
    try:
        if ":" in scale:
            return f"Scale {scale}"
        else:
            return "Scale not given"
    except TypeError:
        return "Scale not given"


def encode_pub_date(pub_year):
    if not pub_year:
        return "    "
    else:
        pub_year = pub_year.replace("[", "").replace("]", "").replace("-", "u")
        return pub_year


def norm_pub_date_text(pub_date):
    if not pub_date:
        return "[date of publication not identified]"
    else:
        return pub_date


def has_true_hyphen(s):
    m = re.compile(r".*\S\-\S.*").match(s)
    if m:
        if "--" in s:
            return False
        else:
            return True
    else:
        return False


def norm_subfield_separator(s):
    """
    ' - ' hypen is usually used as a separator, but there are variations
    """
    if has_true_hyphen(s):
        warnings.warn(f"{s}", SuspiciousDataWarning)

    s = (
        s.replace(" - ", " -- ")
        .replace("- ", "-- ")
        .replace(" -", " --")
        .replace("----", "--")
    )
    return s


def split_subject_elements(s):
    """
    normalizes variation of separating subfields during data entry
    """
    s = norm_subfield_separator(s)
    data = s.split("--")
    return [e.strip() for e in data]


def is_topical_subdivision(sub):
    found = False
    topical = ["history", "discoveries"]
    for s in topical:
        if s in sub.lower():
            found = True
            break
    return found


def is_time_subdivision(sub):
    found = False
    period = ["war"]
    for s in period:
        if s in sub.lower():
            found = True
            break
    return found


def has_invalid_last_chr(sub):
    pattern = re.compile(r".*[\s.,;]$")
    if pattern.match(sub):
        return True
    else:
        return False


def norm_last_subfield(sub):
    while has_invalid_last_chr(sub):
        sub = sub[:-1]
    return f"{sub}."


def construct_geo_subject_subfields(s):
    """
    Generates subject subfields for 651 tag as a pymarc list
    """
    elems = split_subject_elements(s)

    subA = elems[0]
    subV = elems[-1]

    if len(elems) == 1:
        subA = norm_last_subfield(subA)

    subV = norm_last_subfield(subV)

    if len(elems) > 2:
        other_subs = elems[1:-1]
    else:
        other_subs = []

    subfields = []
    subfields.extend(["a", subA])
    if other_subs:
        for sub in other_subs:
            if is_topical_subdivision(sub):
                subfields.extend(["x", sub])
            elif is_time_subdivision(sub):
                subfields.extend(["y", sub])
            else:
                subfields.extend(["z", sub])

    if len(elems) > 1:
        subfields.extend(["v", f"{subV}"])
    return subfields


def construct_topical_subject_subfields(s):
    """
    Creates list of subfield for 650 tag
    """
    pass


def encode_subjects(sub_str):
    fields = []
    subjects = sub_str.split(";")
    for s in subjects:
        subfields = construct_geo_subject_subfields(s)
        fields.append(Field(tag="650", indicators=[" ", "0"], subfields=subfields))
    return fields


def make_bib(row: namedtuple, sequence: int):
    bib = Record()
    # leader
    bib.leader = "00000cem a2200000Mi 4500"

    tags = []

    # 001 tag
    tags.append(Field(tag="001", data=f"bkops-map-{sequence}"))

    # 003 tag
    tags.append(Field(tag="003", data="BookOps"))

    # 005 tag

    timestamp = create_timestamp()
    tags.append(Field(tag="005", data=timestamp))

    # 007 tag

    tags.append(
        Field(
            tag="007",
            data="aj canzn",
        )
    )

    # 008 tag
    dateCreated = date.strftime(date.today(), "%y%m%d")
    pub_year = encode_pub_year(row.pub_year)
    data = f"{dateCreated}s{pub_year}    xx |||||| a  |  |   und d"
    tags.append(Field(tag="008", data=data))

    # 034 tag

    esc = encode_scale(row.scale)
    if esc is not None:
        tags.append(
            Field(tag="034", indicators=["1", " "], subfields=["a", "a", "b", esc])
        )

    # 110 tag

    tags.append(
        Field(
            tag="110",
            indicators=["1", " "],
            subfields=["a", f"{row.author},", "e", "cartographer."],
        )
    )

    # 245 tag

    tags.append(
        Field(tag="245", indicators=["1", "0"], subfields=["a", f"{row.title}."])
    )

    # 246 tag
    if row.alt_title:
        tags.append(
            Field(tag="246", indicators=["3", " "], subfields=["a", row.alt_title])
        )

    # 255 tag

    nsc = norm_scale(row.scale)
    tags.append(Field(tag="255", indicators=[" ", " "], subfields=["a", nsc]))

    # 264 tag

    npub_date = norm_pub_date(row.pub_year)
    tags.append(
        Field(
            tag="264",
            indicators=[" ", "1"],
            subfields=[
                "a",
                "[Place of publication not identified] :",
                "b",
                f"{row.author},",
                "c",
                npub_date,
            ],
        )
    )

    # tag 300
    tags.append(
        Field(
            tag="300",
            indicators=[" ", " "],
            subfields=["a", "1 folded map :", "b", "color"],
        )
    )

    tags.append(
        Field(
            tag="336",
            indicators=[" ", " "],
            subfields=["a", "cartographic image", "b", "cri", "2", "rdacontent"],
        )
    )
    tags.append(
        Field(
            tag="337",
            indicators=[" ", " "],
            subfields=["a", "unmediated", "b", "n", "2", "rddcontent"],
        )
    )
    tags.append(
        Field(
            tag="338",
            indicators=[" ", " "],
            subfields=["a", "sheet", "b", "nb", "2", "rdacontent"],
        )
    )

    # 490 tag
    if row.series:
        tags.append(
            Field(tag="490", indicators=["0", " "], subfields=["a", row.series])
        )

    # 500 tag
    if row.note:
        tags.append(
            Field(tag="500", indicators=[" ", " "], subfields=["a", f"{row.note}."])
        )

    # 505 tag

    if row.content:
        tags.append(
            Field(tag="505", indicators=["0", " "], subfields=["a", f"{row.content}."])
        )

    # 650 tags
    if row.subjects:
        subject_fields = encode_subjects(row.subjects)
        tags.extend(subject_fields)

    # 655 tag
    if row.genre:
        tags.append(
            Field(
                tag="655",
                indicators=[" ", "7"],
                subfields=["a", f"{row.genre}.", "2", "lcgft"],
            )
        )

    # tag 852
    if row.call_number:
        tags.append(
            Field(tag="852", indicators=["8", " "], subfields=["h", row.call_number])
        )

    for t in tags:
        bib.add_ordered_field(t)
    return bib


def source_reader(fh: str):
    for row in map(MapData._make, csv.reader(open(fh, "r"))):
        if row.barcode != "Barcode":
            yield row


def create_bibs(src_fh: str, out_fh: str, start_sequence: int):
    reader = source_reader(src_fh)
    sequence = start_sequence
    for row in reader:
        s = determine_sequence(sequence)
        bib = make_bib(row, s)
        print(bib)
        save2marc(out_fh, bib)
        sequence += 1


if __name__ == "__main__":
    src_fh = "./files/Folded maps for inventory records (Draft) - Sheet1.csv"
    out_fh = "./files/folded_maps.mrc"
    create_bibs(src_fh, out_fh, 1)
