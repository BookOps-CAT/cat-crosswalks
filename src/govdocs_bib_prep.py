"""
Preps OCLC provided MARC records for Government Document resources for import to
Sierra.
"""

import warnings

from bookops_marc import SierraBibReader
from pymarc import Field, Subfield, Indicators

from utils import save2marc


def is_serial(leader: str) -> bool:
    if leader[7] in ("b", "i", "s"):
        return True
    else:
        return False


def construct_callno(value: str) -> Field:
    return Field(
        tag="852",
        indicators=Indicators("8", "0"),
        subfields=[Subfield(code="h", value=f"GPO Internet {value}")],
    )


def construct_command_field() -> Field:
    return Field(
        tag="949",
        indicators=Indicators(" ", " "),
        subfields=[Subfield(code="a", value=f"*bn=ia,iarch;b2=w;")],
    )


def prep_bibs(marcfile: str, out: str) -> None:
    with open(marcfile, "rb") as f:
        reader = SierraBibReader(f, library="nypl")
        for bib in reader:
            bib.normalize_oclc_control_number()
            bib.remove_unsupported_subjects()

            try:
                gpo_class = bib["086"]["a"].strip()
            except (KeyError, AttributeError):
                gpo_class = None
                warnings.warn(f"Record {bib["001"].data} lacks 086 classification")

            callNo_field = construct_callno(gpo_class)
            bib.add_ordered_field(callNo_field)
            command_field = construct_command_field()
            bib.add_ordered_field(command_field)

            if is_serial(bib.leader):
                save2marc(f"{out}-ser.mrc", bib)
            else:
                save2marc(f"{out}-mon.mrc", bib)


if __name__ == "__main__":
    src = "src/files/GovDocs/private/GovDocs-eres-matched.mrc"
    out = "src/files/GovDocs/private/GovDocs-eres-matched-PRC"

    prep_bibs(src, out)
