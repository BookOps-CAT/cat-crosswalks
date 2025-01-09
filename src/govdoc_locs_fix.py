"""
A script restoring original Bib Location codes and inserts correct 910s in MARC records based on data dump before updates.
"""

import csv

from pymarc import MARCReader, Record, Field, Subfield, Indicators

try:
    from utils import save2marc
except ImportError:
    from .utils import save2marc


def cleanup_locs(value: str) -> str:
    """
    Removes invalid Bib Location codes and normalizes them.
    """
    loc_lst = value.split("@")
    new_locs = set()
    for loc in loc_lst:
        if loc not in ["ia", "iarch", "slr", "iaslr"]:
            new_locs.add(loc)
    return ",".join(sorted(list(new_locs)))


def get_bibs2update(csvfile: str) -> dict:
    """
    Parses previously selected list of Sierra bib numbers, locations,
    and material types to be used for selection of appropriate MARC
    records and updating Bib Locations and 910s.
    """
    bibs2update = dict()
    with open(csvfile, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            locs = cleanup_locs(row[1])
            bibs2update[row[0][1:]] = (locs, row[2].strip())
    return bibs2update


def process_bib(bib: Record, bibs2update: dict) -> None:
    """
    Makes appropriate changes to given bib: sets Bib Location and 910
    """
    pass


def process_batch(marcfile: str, csvfile: str, out: str) -> None:
    bibs2update = get_bibs2update(csvfile)
    with open(marcfile, "rb") as f:
        reader = MARCReader(f)
        for bib in reader:
            controlNo = bib["001"].data
            new_controlNo = controlNo.replace("marcive", "").strip()
            bib["001"].data = new_controlNo

            if bib["998"]["c"] in ["s", "i", "b"]:
                bib_type = "ser"
            else:
                bib_type = "mono"

            bibNo = bib["907"]["a"][1:]
            if bibNo in bibs2update:
                locs = bibs2update[bibNo][0]
                mat_type = bibs2update[bibNo][1]
                bib.add_field(
                    Field(
                        tag="949",
                        indicators=Indicators(" ", " "),
                        subfields=[
                            Subfield(
                                code="a", value=f"*b2={mat_type.strip()};bn={locs};"
                            )
                        ],
                    )
                )
                bib.remove_fields("909", "910")
                bib.add_field(
                    Field(
                        tag="910",
                        indicators=Indicators(" ", " "),
                        subfields=[Subfield(code="a", value="RL")],
                    )
                )
                save2marc(f"{out}-{bib_type}.mrc", bib)


if __name__ == "__main__":
    csvfile = "src/files/GovDocs/public/MARCIVE-bibNo-0-locs.csv"
    marcfile = "src/files/GovDocs/private/batch-0.mrc"
    out = "src/files/GovDocs/private/MARCIVE-fixed-batch-0"

    process_batch(marcfile, csvfile, out)
