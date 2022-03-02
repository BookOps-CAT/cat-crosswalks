"""
Script to process Flourish vendor records (scores) and prepare them for
loading into Sierra

To run the script, open your command-line tool, and enter:
$ python src/flourish_bibs.py [src MARC file path]

"""
import csv
import os
import sys
from typing import Optional

from pymarc import Field, MARCReader, Record

from utils import save2marc, save2csv


def processed_file_path(file: str, suffix: str) -> str:
    """
    Creates a file path for processed records.
    The path points to the same folder as source file, has the
    same base name, but is altered with 'PRC' suffix.

    Args:
        file:                   source marc file path
        suffix:                 string to append to file name

    Returns:
        path to processed marc file
    """
    head, tail = os.path.split(file)
    base_name = tail[:-4]
    return os.path.join(head, f"{base_name}-{suffix}.mrc")


def flip_911(bib: Record) -> None:
    """
    Removes any 911 tags and adds 910 RL

    Args:
        bib:                    `pymarc.Record` instance
    """
    bib.remove_fields("911")
    bib.remove_fields("910")
    if bib.get_fields("910") == []:
        bib.add_ordered_field(
            Field(tag="910", indicators=[" ", " "], subfields=["a", "RL"])
        )


def get_call_no(bib: Record) -> Optional[str]:
    """
    Parses reseach call number in 852$h.

    Args:
        bib:                    `pymarc.Record` instance

    Returns:
        research call number
    """
    for tag in bib.get_fields("852"):
        if tag.indicator1 == "8":
            try:
                return tag["h"].strip()
            except AttributeError:
                pass

    print(f"Bib # {bib['001'].data} is missing correct 852 tag.")


def add_command_tag(bib: Record) -> None:
    """
    Adds 949 command tag specifying sierra bib material type, bib code 3,
    load table to be used and default location.

    Args:
        bib:                    `pymarc.Record` instance
    """
    bib.add_ordered_field(
        Field(
            tag="949",
            indicators=[" ", " "],
            subfields=["a", "*b2=c;b3=h;recs=flourish;bn=xxx;"],
        )
    )


def add_oclc_fields(bib: Record) -> None:
    """
    Adds 035 field to provided bib with OCLC #

    Args:
        bib:                    `pymarc.Record` instance
    """

    controlNo = bib["001"].data.strip()
    bib.add_ordered_field(Field(tag="003", data="OCoLC"))
    bib.add_ordered_field(
        Field(tag="035", indicators=[" ", " "], subfields=["a", f"(OCoLC){controlNo}"])
    )


def create_item_tag(bib: Record, callno: str) -> None:
    """
    Creates item record field in provided bib.

    Args:
        bib:                    `pymarc.Record` instance
        callno:                 research call number string
    """

    # fmt: off
    if callno is not None:
        bib.add_ordered_field(
            Field(
                tag="949",
                indicators=[" ", "1"],
                subfields=[
                    "z", "8528",
                    "a", callno,
                    "i", "BARCODE TO BE SUPPLIED",
                    "l", "mym38",
                    "t", "7",
                    "h", "32",
                    "o", "1",
                    "s", "-",
                    "v", "MUS/",
                ],
            )
        )
        # fmt: on


def process(file: str) -> None:
    """
    Launches manipulation of record found in given file.

    Args:
        file:               path to MARC file to be processed
    """
    # load control number "registry"
    try:
        with open("src/flourish-registry.csv", "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            registry = set([row[0] for row in reader])
    except FileNotFoundError:
        registry = set()
        print("Creating control number registry file.")

    proc_file = processed_file_path(file, suffix="PRC")
    dup_file = processed_file_path(file, suffix="DUP")
    err_file = processed_file_path(file, suffix="ERR")

    # to avoid appending the same records to a file by accident
    # the script deletes PRC files if found
    try:
        os.remove(proc_file)
    except FileNotFoundError:
        pass

    with open(file, "rb") as marcfile:
        reader = MARCReader(marcfile)
        p = 0
        d = 0
        for bib in reader:

            add_oclc_fields(bib)
            flip_911(bib)
            add_command_tag(bib)

            callno = get_call_no(bib)
            create_item_tag(bib, callno)

            # check in the control number "registry" if not duplicate
            control_no = bib["001"].data.strip()
            if callno is None:
                print(f"Isolating bib without call number (oclc # {control_no})")
                save2marc(err_file, bib)

            elif control_no not in registry:
                save2marc(proc_file, bib)
                save2csv("src/flourish-registry.csv", [control_no, callno, file])
                registry.add(control_no)
                p += 1
            else:
                d += 1
                save2marc(dup_file, bib)
                print(f"Found duplicate control # {control_no} in the file.")

    print(f"Total # of records in src file: {p + d}.")
    print(f"{p} records have been maniuplated and saved to {proc_file}")
    print(f"Found {d} duplicate records.")


if __name__ == "__main__":
    process(sys.argv[1])
