"""
Use to enrich with 505 note (song index) score records
"""
from collections import namedtuple
import csv
import json
import os
from typing import Optional

from bookops_worldcat import WorldcatAccessToken, MetadataSession
from pymarc import MARCReader, Record


if __name__ == "__main__":
    from utils import save2csv
else:
    from src.utils import save2csv


BibData = namedtuple(
    "BibData",
    [
        "bibNo",
        "title",
        "pubDate",
        "oclcNo",
        "lccn",
        "isbn",
        "standardNo",
        "publisherNo",
    ],
    defaults=[None, None, None, None, [], [], []],
)


def bib_reader(fh: str) -> Record:
    with open(fh, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            yield bib


def save2marc(out: str, bib: Record) -> None:
    with open(out, "ab") as marcfile:
        marcfile.write(bib.as_marc())


def categorize_bib(bib: Record) -> None:
    content_tag = bib["505"]
    base_dir = "./files/SongIndex"
    if not content_tag:
        out = f"{base_dir}/no-505.mrc"
    elif content_tag.indicator2 == " ":
        out = f"{base_dir}/basic-505.mrc"
    elif content_tag.indicator2 == "0":
        out = f"{base_dir}/enhanced-505.mrc"
    else:
        out = f"{base_dir}/unidentified-505.mrc"

    with open(out, "ab") as marcfile:
        marcfile.write(bib.as_marc())


def get_oclc_no(bib: Record) -> Optional[str]:
    if bib["003"] and "OCoLC" in bib["003"].data:
        oclc_no = (
            bib["001"]
            .data.replace("ocn", "")
            .replace("ocm", "")
            .replace("on", "")
            .strip()
        )
        if oclc_no.isdigit():
            return oclc_no
        else:
            return None
    fields = bib.get_fields("035")
    for f in fields:
        if "(OCoLC)" in f.value():
            oclc_no = f["a"].replace("(OCoLC)", "").strip()
            if oclc_no.isdigit():
                return oclc_no
            else:
                return None

    if bib["991"]:
        oclc_no = bib["991"].value().strip()
        if oclc_no.isdigit():
            return oclc_no
        else:
            return None


def get_lccn(bib: Record) -> Optional[str]:
    try:
        return bib["010"]["a"].strip()
    except (TypeError, AttributeError):
        return None


def get_isbns(bib: Record) -> list:
    isbns = []
    fields = bib.get_fields("020")
    for f in fields:
        if "a" in f:
            value = f["a"].strip()
            value = value.split(" ")
            isbns.append(value[0])
    return isbns


def get_standard_nos(bib: Record) -> list:
    standard_nos = []
    fields = bib.get_fields("024")
    for f in fields:
        if "a" in f:
            standard_nos.append(f["a"].strip())
    return standard_nos


def get_publisher_nos(bib: Record) -> list:
    publisher_nos = []
    fields = bib.get_fields("028")
    for f in fields:
        if "a" in f:
            publisher_nos.append(f["a"].strip())
    return publisher_nos


def parse4query(out: str, bib: Record) -> None:
    """
    Creates a csv file with data that can be used to
    query Worldcat.
    """
    bibNo = bib["907"]["a"][1:]
    title = bib["245"]["a"].replace(":", "").replace("/", "").strip().lower()
    pubDate = bib["008"][7:10]
    oclcNo = get_oclc_no(bib)
    lccn = get_lccn(bib)
    isbn = get_isbns(bib)
    standardNo = get_standard_nos(bib)
    publisherNo = get_publisher_nos(bib)

    data = BibData(bibNo, title, pubDate, oclcNo, lccn, isbn, standardNo, publisherNo)
    save2csv(out, data)


def get_token():
    fh = os.path.join(os.environ.get("USERPROFILE"), ".oclc/nyp_overload.json")
    with open(fh, "r") as f:
        creds = json.load(f)
        token = WorldcatAccessToken(
            key=creds["key"],
            secret=creds["secret"],
            principal_id=creds["principal_id"],
            principal_idns=creds["principal_idns"],
            scopes="WorldCatMetadataAPI",
        )
        return token


def query_worldcat(session: MetadataSession, query_data: BibData) -> None:
    payload = dict(
        inCatalogLanguage="eng",
        itemType="",
        itemSubType="",
        orderBy="mostWidelyHeld",
        limit=1,
    )
    if query_data.oclcNo is not None:
        result = session.get_brief_bib(query_data.oclcNo)
    elif query_data.lccn is not None:
        result = session.search_brief_bibs(q=f"ln:{query_data.lccn}", **payload)
    elif query_data.isbn:
        for i in query_data.isbn:
            result = session.search_brief_bibs(q=f"bn:{i}", **payload)
            if result.status_code == 200:
                break
    elif query_data.standardNo:
        for s in query_data.standardNo:
            result = session.search_brief_bibs(q=f"sn={s}", **payload)


if __name__ == "__main__":
    # fin = "./files/SongIndex/no-505.mrc"
    # fout = "./files/SongIndex/query_data.csv"
    # reader = bib_reader(fin)
    # for bib in reader:
    #     parse4query(fout, bib)
    token = get_token()
    session = MetadataSession(authorization=token)

    with open("./files/SongIndex/query_data.csv", "r", encoding="utf8") as f:
        reader = csv.reader(f)
        for row in reader:
            data = BibData(row)
            result = query_worldcat(session, data)
            if result is not None:
                print(result.status_code)
                print(result.json())
                break

    session.close()
