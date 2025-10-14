import csv

from pymarc import MARCReader, Record, Field, Subfield, Indicators

from utils import save2marc


def get_updated_oclc_numbers(fh: str) -> dict[str, str]:
    bibNos = dict()
    with open(fh, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            bibNos[row[0]] = row[1]
    return bibNos


def update_controlno_field(bib: Record, new_value: str) -> None:
    bib["001"].data = new_value


def add_mat_type(bib, value: str):
    bib.add_ordered_field(
        Field(
            tag="949",
            indicators=Indicators(" ", " "),
            subfields=[Subfield(code="a", value=f"*b2={value};")],
        )
    )


def process_marc(fh: str, updates: dict[str, str]) -> None:
    with open(fh, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            bibNo = bib["907"]["a"][1:]
            bib_level = bib["998"]["c"].strip()
            mat_type = bib["998"]["d"].strip()

            if bibNo in updates:
                bib.remove_fields("852")
                update_controlno_field(bib, updates[bibNo])
                add_mat_type(bib, mat_type)
                if bib_level in "b,i,s":
                    # serials
                    save2marc(
                        "src/files/GovDocs/private/GovDocs-updated-oclc-number-serials.mrc",
                        bib,
                    )
                else:
                    save2marc(
                        "src/files/GovDocs/private/GovDocs-updated-oclc-number-mono.mrc",
                        bib,
                    )


if __name__ == "__main__":
    marcfile = "src/files/GovDocs/private/GovDocs-changed-oclc-number.mrc"
    oclc_fh = "src/files/GovDocs/private/GovDocs-only-Sierra-changed.csv"
    updates = get_updated_oclc_numbers(oclc_fh)
    process_marc(marcfile, updates)
