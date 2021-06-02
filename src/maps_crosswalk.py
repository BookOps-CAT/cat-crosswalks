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
        "t600",
        "t610",
        "t611",
        "t650",
        "t651",
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


def construct_subject_subfields(s):
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


def identify_t100_subfield_q_position(s):
    try:
        start = s.index("(")
        end = s.index(")")
        return (start, end + 1)
    except ValueError:
        return None


def identify_t100_subfield_q(s, pos):
    try:
        start, end = pos
        return s[start : end + 1].strip()
    except TypeError:
        return None


def identify_t100_subfield_d_position(s, sub_d):
    if sub_d:
        return s.index(sub_d)
    else:
        return None


def identify_t100_subfield_d(s):
    p = re.compile(r".*,\s(.*\d{2,})$")
    m = p.match(s)
    if m:
        return m.group(1)
    else:
        return None


def add_preceding_comma_to_last_subfield(subfields):
    last = subfields[-1].strip()
    new_subfields = subfields[:-1]
    new_subfields.append(f"{last},")
    return new_subfields


def construct_personal_author_subfields(s):
    """
    Subfields for tag 100
    """
    subfields = []

    sub_d = identify_t100_subfield_d(s)
    pos_d = identify_t100_subfield_d_position(s, sub_d)

    pos_q = identify_t100_subfield_q_position(s)
    sub_q = identify_t100_subfield_q(s, pos_q)

    if sub_q:
        sub_a = s[: pos_q[0]].strip()
    elif sub_d:
        sub_a = s[:pos_d].strip()
    else:
        sub_a = s[:].strip()

    subfields.extend(["a", sub_a])
    if sub_q:
        subfields.extend(["q", sub_q])
    if sub_d:
        subfields.extend(["d", sub_d])

    final_subfields = add_preceding_comma_to_last_subfield(subfields)

    final_subfields.extend(["e", "cartographer."])
    return final_subfields


def construct_corporate_author_subfields(s):
    """
    Subfields for 110 tag
    """
    subfields = add_preceding_comma_to_last_subfield(["a", s])
    subfields.extend(["e", "cartographer."])
    return subfields


def subject_indicators(tag):
    if tag == "600":
        indicators = ["1", "0"]
    elif tag == "610":
        indicators = ["2", "0"]
    elif tag == "611":
        indicators = ["2", "0"]
    else:
        indicators = [" ", "0"]
    return indicators


def encode_subjects(sub_str, tag):

    indicators = subject_indicators(tag)

    fields = []
    subjects = [s.strip() for s in sub_str.split(";") if s.strip() != ""]
    for s in subjects:
        subfields = construct_subject_subfields(s)
        fields.append(Field(tag=tag, indicators=indicators, subfields=subfields))
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
    pub_year = encode_pub_date(row.t260)
    data = f"{dateCreated}s{pub_year}    xx |||||| a  |  |   und d"
    tags.append(Field(tag="008", data=data))

    # 034 tag

    esc = encode_scale(row.t255)
    if esc is not None:
        tags.append(
            Field(tag="034", indicators=["1", " "], subfields=["a", "a", "b", esc])
        )

    # 100 tag
    if row.t100:
        subfields = construct_personal_author_subfields(row.t100)
        tags.append(Field(tag="100", indicators=["1", " "], subfields=subfields))

    # 110 tag
    if row.t110 and not row.t100:
        subfields = construct_corporate_author_subfields(row.t110)
        tags.append(
            Field(
                tag="110",
                indicators=["1", " "],
                subfields=subfields,
            )
        )

    # 245 tag
    tags.append(
        Field(tag="245", indicators=["1", "0"], subfields=["a", f"{row.t245.strip()}."])
    )

    # 246 tag
    if row.t246:
        tags.append(
            Field(tag="246", indicators=["3", " "], subfields=["a", row.t246.strip()])
        )

    # 250 tag
    if row.t250:
        tags.append(
            Field(tag="250", indicators=[" ", " "], subfields=["a", row.t250.strip()])
        )

    # 255 tag
    nsc = norm_scale_text(row.t255)
    tags.append(Field(tag="255", indicators=[" ", " "], subfields=["a", nsc]))

    # 264 tag
    # if row.t100:
    #     publisher = row.t100.strip()
    if row.t110:
        publisher = row.t110.strip()
    else:
        publisher = "[Publisher not identified]"
    npub_date = norm_pub_date_text(row.t260)

    tags.append(
        Field(
            tag="264",
            indicators=[" ", "1"],
            subfields=[
                "a",
                "[Place of publication not identified] :",
                "b",
                f"{publisher},",
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
    if row.t490:
        tags.append(
            Field(tag="490", indicators=["0", " "], subfields=["a", row.t490.strip()])
        )

    # 500 tag
    if row.t500:
        tags.append(
            Field(
                tag="500",
                indicators=[" ", " "],
                subfields=["a", f"{row.t500.strip()}."],
            )
        )

    # 505 tag
    if row.t505:
        tags.append(
            Field(
                tag="505",
                indicators=["0", " "],
                subfields=["a", f"{row.t505.strip()}."],
            )
        )

    # 600 tags
    if row.t600:
        subject_fields = encode_subjects(row.t600, "600")
        tags.extend(subject_fields)

    # 610 tags
    if row.t610:
        subject_fields = encode_subjects(row.t610, "610")
        tags.extend(subject_fields)

    # 611 tags
    if row.t611:
        subject_fields = encode_subjects(row.t611, "611")
        tags.extend(subject_fields)

    # 650 tags
    if row.t650:
        subject_fields = encode_subjects(row.t650, "650")
        tags.extend(subject_fields)

    # 651 tags
    if row.t651:
        subject_fields = encode_subjects(row.t651, "651")
        tags.extend(subject_fields)

    # 655 tag
    if row.t655:
        tags.append(
            Field(
                tag="655",
                indicators=[" ", "7"],
                subfields=["a", f"{row.t655}.", "2", "lcgft"],
            )
        )

    # tag 852
    if row.t852:
        tags.append(
            Field(tag="852", indicators=["8", " "], subfields=["h", row.t852.strip()])
        )

    for t in tags:
        bib.add_ordered_field(t)
    return bib


def source_reader(fh: str):
    for row in map(MapData._make, csv.reader(open(fh, "r", encoding="utf-8"))):
        if row.barcode != "Barcode":
            yield row


def create_bibs(src_fh: str, out_fh: str, start_sequence: int):
    reader = source_reader(src_fh)
    sequence = start_sequence
    for row in reader:
        s = determine_control_number_sequence(sequence)
        bib = make_bib(row, s)
        save2marc(out_fh, bib)
        sequence += 1


if __name__ == "__main__":
    src_fh = "../files/pre 1900 Folded maps for inventory records - Sheet1.csv"
    out_fh = "../files/folded_maps.mrc"
    create_bibs(src_fh, out_fh, 1)
