"""
A set of scripts to be used to enahance records exported from Sierra with data from Worldcat
"""
from io import BytesIO
import json
import logging
import os
import sys

from bookops_worldcat import WorldcatAccessToken, MetadataSession
from pymarc import Field, Record, MARCReader, parse_xml_to_array


def get_creds(creds_fh):
    with open(creds_fh, "r") as f:
        creds = json.load(f)
        return creds


def get_token(key, secret, scope, principal_id, principal_idns):
    token = WorldcatAccessToken(
        key=key,
        secret=secret,
        scopes=scope,
        principal_id=principal_id,
        principal_idns=principal_idns,
    )
    return token


def is_oclc_no(value: str) -> bool:
    if value is None:
        return False

    prefixes = ["ocm", "ocn", "on"]
    for prefix in prefixes:
        if prefix in value[:3]:
            return True


def parse_identifiers(bib: Record):
    bib_no = bib["907"]["a"][1:]
    if "001" in bib:
        control_no = bib["001"].data.strip()
    else:
        control_no = None
    if "010" in bib:
        lc_no = bib["010"].value().strip()
    else:
        lc_no = None

    author = bib.author()

    t245 = bib["245"]
    start = int(t245.indicator2)
    title = t245["a"][start:].strip()

    if "008" in bib:
        pubyear = bib["008"][7:10]
    else:
        pubyear = None

    bib_format = bib["998"]["d"][0]
    opac = bib["998"]["e"]

    return (bib_no, control_no, lc_no, author, title, pubyear, bib_format, opac)


def response_has_isbn(response):
    if "isbns" in response:
        return True
    else:
        return False


def oclc_no_query(session, oclc_no):
    response = session.get_brief_bib(oclc_no)
    return response.json()


def get_current_oclc_no(response):
    return response["oclcNumber"]


def get_full_bib(session, oclc_no):
    response = session.get_full_bib(oclc_no)
    data = BytesIO(response.content)
    bib = parse_xml_to_array(data)[0]
    return bib


def save2marc(bib, out):
    with open(out, "ab") as marcfile:
        marcfile.write(bib.as_marc())


def prepare_bib(bib, bib_no, bib_format_code, opac):

    # remove unsupported subject terms
    subjects = bib.subjects()
    for field in subjects:
        if field.tag.startswith("69"):
            bib.remove_field(field)
        elif field.indicator2 == "0":
            pass
        elif field.indicator2 == "7":
            terms_src = field["2"]
            if terms_src.lower() in ("lcsh", "fast", "gsafd", "lcgft", "lctgm"):
                pass
            else:
                bib.remove_field(field)

    # add bib # matchopoint
    bib.add_ordered_field(
        Field(tag="907", indicators=[" ", " "], subfields=["a", f".{bib_no}"])
    )

    # add initiatls
    bib.add_ordered_field(
        Field(tag="947", indicators=[" ", " "], subfields=["a", "tak/bot"])
    )

    # add command tag
    commands = []
    commands.append(f"b2={bib_format_code}")
    if opac != "-":
        commands.append(f"b3={opac}")
    command_str = ";".join(commands)
    bib.add_ordered_field(
        Field(tag="949", indicators=[" ", " "], subfields=["a", f"*{command_str};"])
    )


def enhance(marc_fh: str) -> None:
    """
    Use to launch enhancing process
    """
    # out files
    enhanced_fh = f"{marc_fh[:-4]}-ENHANCED.mrc"
    skipped_fh = f"{marc_fh[:-4]}-SKIPPED.mrc"

    logging.info("Obtaining Worldcat access token.")
    creds_fh = os.path.join(os.environ["USERPROFILE"], ".oclc/bpl_overload.json")
    creds = get_creds(creds_fh)
    token = get_token(
        creds["key"],
        creds["secret"],
        "WorldCatMetadataAPI",
        creds["principal_id"],
        creds["principal_idns"],
    )

    logging.info("Opening Worldcat session...")
    with MetadataSession(authorization=token) as session:

        logging.info("Reading src marc file...")
        with open(marc_fh, "rb") as fin:
            reader = MARCReader(fin)
            n = 0
            o = 0
            l = 0
            i = 0
            for bib in reader:
                n += 1

                (
                    bib_no,
                    control_no,
                    lc_no,
                    author,
                    title,
                    pubyear,
                    bib_format,
                    opac,
                ) = parse_identifiers(bib)
                logging.debug(f"{bib_no}=cn:{control_no}, ln:{lc_no}")

                if is_oclc_no(control_no):
                    o += 1
                    response = oclc_no_query(session, control_no)
                    if response_has_isbn(response):
                        i += 1
                        oclc_no = get_current_oclc_no(response)
                        worldcat_bib = get_full_bib(session, oclc_no)
                        prepare_bib(worldcat_bib, bib_no, bib_format, opac)
                        save2marc(worldcat_bib, enhanced_fh)
                else:
                    save2marc(bib, skipped_fh)

                if not is_oclc_no(control_no) and lc_no is not None:
                    l += 1

                print(f"Processing record {n}.")

    logging.info(
        f"Found {n} bibs in {marc_fh}. The set includs {o} oclc # and {l} lccn."
    )
    logging.info(f"Successfuly enhanced {i} bibs.")


if __name__ == "__main__":

    logging.basicConfig(
        filename="enhance_log.log",
        filemode="w",
        level=logging.DEBUG,
        format="%(levelname)s:%(asctime)s:%(message)s",
    )
    logging.info("Launching enhancing process...")

    enhance(sys.argv[1])
