"""
mapping based on:
https://docs.google.com/spreadsheets/d/10Cd4cv8W-ijKF6pyp7MQleWn2ExGL2sRXd-tz0BpWpE/edit#gid=541205052
"""

import csv
from datetime import date

from pymarc import Record, Field

from utils import save2marc


fh = "./files/CGD data - Sheet1.csv"
with open(fh, "r") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # skip the header
    for row in reader:
        bib = Record()

        # leader
        bib.leader = "00000nam a2200000ui 4500"

        # 008
        dateCreated = date.strftime(date.today(), "%y%m%d")
        data = f"{dateCreated}s2021    nyu           000 u eng d"
        bib.add_field(Field(tag="008", data=data))

        # 020
        isbn = row[14].strip()
        if isbn:
            bib.add_field(
                Field(tag="020", indicators=[" ", " "], subfields=["a", isbn])
            )

        # 035
        oclc = row[12].strip()
        bib.add_field(
            Field(tag="035", indicators=[" ", " "], subfields=["a", f"(OCoLC){oclc}"])
        )

        # 245
        title = row[16].strip()
        bib.add_field(Field(tag="245", indicators=["0", "0"], subfields=["a", title]))

        # 500
        note = f"Starting CGD: {row[2].strip()}."
        bib.add_field(Field(tag="500", indicators=[" ", " "], subfields=["a", note]))

        # item record
        item = row[1].strip()
        call_number = f"ReCAP {item}"

        # 852
        loc = row[8].strip()
        item_agency = row[10].strip()
        bib.add_field(
            Field(
                tag="852",
                indicators=[" ", " "],
                subfields=["h", call_number, "b", loc, "y", item_agency],
            )
        )

        # 876
        opac_msg = row[9].strip()
        item_type = str(row[7]).strip()
        barcode = row[5].strip()

        # fmt: off
        bib.add_field(
            Field(
                tag="876",
                indicators=[" ", " "],
                subfields=[
                    "o", opac_msg,
                    "y", item_type,
                    "k", loc,
                    "p", barcode,
                    "s", item_agency,
                    "j", "-",  # status
                    "t", "1",  # copies
                ],
            )
        )
        # fmt: on

        save2marc("./files/nypl-cgd-testing-083021.mrc", bib)
