"""
Script to reclassify bibs and item records of the Library of America collection
"""

import csv
import json
import os
from typing import Generator, Union

from bookops_sierra import SierraSession, SierraToken

from src.utils import save2csv

# Source data


def get_reclass_data(fh: str) -> Generator[[str], None, None]:
    with open(fh, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            bibNo = row[0].strip()[1:-1]
            yield (bibNo)


# Sierra API


def connect2sierra():
    # test Sierra evn!
    fh = os.path.join(os.environ["USERPROFILE"], ".cred/.sierra/sierra-dev.json")
    with open(fh, "r") as file:
        cred = json.load(file)
    token = SierraToken(
        client_id=cred["client_id"],
        client_secret=cred["client_secret"],
        host_url=cred["host_url"],
        agent="BOOKOPS/TESTS",
    )
    with SierraSession(authorization=token, timeout=10) as session:
        return session


def get_bib(sid: Union[str, int], conn: SierraSession) -> dict:
    res = conn.bib_get(sid, fields="varFields,items")
    # print(f"Server response code: {res.status_code}")
    return res.json()


def get_item_nos_from_bib_response(urls: list[str]) -> list[str]:
    return [u.rsplit("/", 1)[-1] for u in urls]


def get_items(sids: str, conn: SierraSession) -> list[dict]:
    res = conn.items_get(sids=sids, fields="location,varFields")
    print(f"Item request: {res.url}")
    items = res.json()["entries"]
    return items


def update_bib(sid: Union[str, int], data: dict, conn: SierraSession) -> int:
    out = conn.bib_update(sid=sid, data=data, data_format="application/json")
    # print(f"Update response code: {out.status_code}")
    return out.status_code


# MARC manipulation


def construct_callno_field(subfields: list[dict], fieldTag: str) -> dict:
    if not isinstance(subfields, list):
        raise TypeError("Invalid subfields param. Must be a list of dict.")
    if not isinstance(fieldTag, str):
        raise TypeError("Invalid fieldTag param. Must be a str.")
    return {
        "fieldTag": fieldTag,
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": subfields,
    }


def is_valid_item(item: dict) -> bool:
    """
    Checks if item record belongs to mall1 location and has call number
    starting with *R-RMRR in the subfield $h
    """
    if not isinstance(item, dict):
        raise TypeError("Invalid item param. Must be a dict.")

    valid = []

    if item["location"]["code"] == "mall1":
        valid.append(True)
    else:
        valid.append(False)

    for field in item["varFields"]:
        if field.get("fieldTag") == "c":
            for sub in field.get("subfields", []):
                if sub.get("tag") == "k":
                    if sub.get("content", "").startswith("*R-RMRR"):
                        valid.append(True)
                    else:
                        valid.append(False)
    if all(valid):
        return True
    else:
        return False


def select_050_field(bib: dict) -> dict:
    """
    Selects the 050 field from the bib record. Prefers LC 050 (ind2=0).
    If multiple 050 non-LC fields are present, selects the first one.
    """
    varFields = bib.get("varFields", [])
    for field in varFields:
        if field.get("marcTag") == "050" and field.get("ind2") == "0":
            return field
    else:
        # take the first one
        for field in varFields:
            if field.get("marcTag") == "050":
                return field
    return {}


def get_lcc_subfields_from_bib(bib: dict) -> list[dict]:
    """
    Constructs subfields for the 852 field based on the 050 field.
    """
    src_field = select_050_field(bib)
    new_subfields = []
    if src_field:
        for sub in src_field.get("subfields", []):
            if sub.get("tag") == "a":
                new_subfields.append({"tag": "k", "content": "*R-RMRR"})
                new_subfields.append({"tag": "h", "content": sub.get("content")})
            elif sub.get("tag") == "b":
                new_subfields.append({"tag": "i", "content": sub.get("content")})
        return new_subfields
    else:
        return []


def run(src_fh: str):
    out = "src/files/LOA/loa-report.csv"
    not_valid = "src/files/LOA/loa-not-valid.csv"
    conn = connect2sierra()
    for bibno in get_reclass_data(src_fh):
        bib = get_bib(bibno, conn)
        items = get_item_nos_from_bib_response(bib["items"])
        callNo_subfields = get_lcc_subfields_from_bib(bib)
        bib_callNo_field = construct_callno_field(
            subfields=callNo_subfields, fieldTag="q"
        )

        if callNo_subfields:
            # update 852s
            pass
        else:
            print(f"No LCC found for bib {bibno}")
            save2csv(out, [bibno, "ERROR", "NO LCC FOUND ON BIB"])
            continue

        for itemNo in items:
            item = get_items(itemNo, conn)
            if is_valid_item(item[0]):
                # change the call number field
                callNo_field = construct_callno_field(
                    subfields=callNo_subfields,
                    fieldTag="c",
                )
            else:
                print(f"Item {item} of bib {bibno} is not valid")
                save2csv(not_valid, [bibno, item])
        else:
            save2csv(out, [bibno, "ERROR", "NO ITEM FOUND"])
