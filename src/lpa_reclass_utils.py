import csv
import json
import os
import re
from typing import Union, Optional, Generator
from urllib.parse import urlparse

from bookops_sierra import SierraSession, SierraToken


# SOURCE DATA
def get_reclass_data(fh: str) -> Generator[tuple[str, bool, str], None, None]:
    with open(fh, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            bibNo = row[1].strip()[1:-1]
            spec_cutter = has_special_cutter(row[2])
            lcc = row[3].strip()
            yield (bibNo, spec_cutter, lcc)


def has_special_cutter(value: str) -> bool:
    if "YES" in value.upper():
        return True
    else:
        return False


# SIERRA API methods


def connect2sierra():
    fh = os.path.join(os.environ["USERPROFILE"], ".cred/.sierra/sierra-dev.json")
    with open(fh, "r") as file:
        cred = json.load(file)
    token = SierraToken(
        client_id=cred["client_id"],
        client_secret=cred["client_secret"],
        host_url=cred["host_url"],
        agent="BOOKOPS/TESTS",
    )
    with SierraSession(authorization=token) as session:
        return session


def get_bib(sid: Union[str, int], conn: SierraSession) -> dict:
    res = conn.bib_get(sid, fields="varFields,items")
    print(f"Server response code: {res.status_code}")
    return res.json()


def get_item_nos_from_bib_response(urls: list[str]) -> list[str]:
    return [u.rsplit("/", 1)[-1] for u in urls]


def get_items(sids: str, conn: SierraSession) -> list[dict]:
    res = conn.items_get(sids=sids, fields="location,varFields")
    items = res.json()["entries"]
    return items


def update_bib(sid: Union[str, int], data: dict, conn: SierraSession) -> None:
    out = conn.bib_update(sid=sid, data=data, data_format="application/json")
    print(f"Update response code: {out.status_code}")


# MARC MANIPULATION


def change_varFields(item: dict, lcc: str, lcc_cutter: str) -> list[dict]:
    new_varFields = []
    varFields = item["varFields"]
    for f in varFields:
        if is_callnumber_field(f):
            callnumber = construct_item_callnumber_field(lcc, lcc_cutter)
            new_varFields.append(callnumber)
        else:
            new_varFields.append(f)
    return new_varFields


def construct_item_callnumber_field(lcc: str, lcc_cutter: str) -> dict:
    return {
        "fieldTag": "c",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": [
            {"tag": "h", "content": lcc},
            {"tag": "i", "content": lcc_cutter},
        ],
    }


def construct_lcc_field(subfields: list[dict]) -> dict:
    return {
        "fieldTag": "q",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": subfields,
    }


def construct_subfields_for_lcc(value: str, special_cutter: bool) -> list[dict]:
    if special_cutter:
        subfield_h = value[: value.index(" ")].strip()
        subfield_i = value[value.index(" ") :].strip()
    else:
        subfield_h = value[: value.index(".")].strip()
        subfield_i = value[value.index(".") :].strip()

    return [{"tag": "h", "content": subfield_h}, {"tag": "i", "content": subfield_i}]


def determine_save_to_delete_callnumbers(items: dict) -> set[str]:
    # classmarks belonging to other locations
    other_callnumbers = get_other_item_callnumbers(items)
    # classmarks unique to pam11 & pah11
    ref_callnumbers = get_ref_item_callnumbers(items)

    callnumbers4del = set()
    for callnumber in ref_callnumbers:
        if callnumber not in other_callnumbers:
            callnumbers4del.add(callnumber)

    return callnumbers4del


def get_bib_callnumber(bib: dict) -> set[str]:
    pass


def get_callnumber(field: dict) -> Optional[str]:
    try:
        callnumber = field["subfields"][0]["content"].strip()
    except (KeyError, IndexError):
        return None
    return callnumber


def get_other_item_callnumbers(items: dict) -> set[str]:
    callnumbers = set()
    for i in items:
        if not is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_subfield_contents(f)
                    callnumbers.add(callnumber)
    return callnumbers


def get_ref_item_callnumbers(items: dict) -> set[str]:
    callnumbers = set()
    for i in items:
        if is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_subfield_contents(f)
                    callnumbers.add(callnumber)
    return callnumbers


def get_subfield_contents(var_field: dict) -> str:
    elements = []
    try:
        for subfield in var_field["subfields"]:
            norm_content = normalize_callnumber(subfield["content"])
            elements.append(norm_content)
    except KeyError:
        pass
    return " ".join(elements)


def is_callnumber_field(field: dict) -> bool:
    try:
        if field["marcTag"] == "852" and field["fieldTag"] in ("c", "q"):
            return True
        else:
            return False
    except KeyError:
        return False


def is_callnumber_for_deletion(callnumber: str, callnumbers4del: list[str]) -> bool:
    # print(callnumber, callnumbers4del[0], callnumber in callnumbers4del)
    if callnumber in callnumbers4del:
        return True
    else:
        return False


def is_lpa_ref_location(item: dict) -> bool:
    try:
        if item["location"]["code"] in ("pam11", "pah11"):
            return True
        else:
            return False
    except KeyError:
        return False


def new_callnumber(varFields: list[dict], callnumbers4del: list[str]) -> list:
    new_varFields = []
    for f in varFields:
        if is_callnumber_field(f):
            callnumber = get_callnumber(f)
            if callnumber and is_callnumber_for_deletion(callnumber, callnumbers4del):
                pass
            else:
                new_varFields.append(f)
        else:
            new_varFields.append(f)
    return new_varFields


def normalize_callnumber(value: str) -> str:
    norm_value = re.sub(r'\.|,|\(|\)|"|-', "", value).strip()
    return norm_value
