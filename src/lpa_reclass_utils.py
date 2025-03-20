import csv
from datetime import datetime
import json
import os
import re
from typing import Union, Generator

from bookops_sierra import SierraSession, SierraToken


class MultiCallNumError(Exception):
    pass


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
    fh = os.path.join(os.environ["USERPROFILE"], ".cred/.sierra/sierra-prod-lpa.json")
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


# MARC MANIPULATION


def change_item_varFields(item: dict, callnumber_field: dict) -> list[dict]:
    """
    Returns updated with LCC item varFields
    """
    new_varFields: list[dict] = []
    field_added = False
    for f in item["varFields"]:
        if is_callnumber_field(f) and not field_added:
            # replace existing call number field
            old_callnumber = get_callnumber(f)
            internal_note = construct_item_internal_note(old_callnumber)
            field_added = True
        elif is_callnumber_field(f) and field_added:
            # multiple call number fields encountered!
            # manual corrections needed
            raise MultiCallNumError
        else:
            # keep any not relevant existing fields
            new_varFields.append(f)

    # add if no call number field present
    if not field_added:
        internal_note = construct_item_internal_note("MISSING on item")

    new_varFields.append(callnumber_field)
    new_varFields.append(internal_note)
    return new_varFields


def construct_item_internal_note(value: str):
    return {
        "fieldTag": "x",
        "content": f"Reclassified by CAT/mus, {datetime.now():%Y-%m-%d} (former classmark: {value})",
    }


def construct_lcc_field(subfields: list[dict], fieldTag: str) -> dict:
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


def construct_947_field(value: str) -> dict[str, Union[str, list]]:
    return {
        "fieldTag": "l",
        "marcTag": "947",
        "ind1": " ",
        "ind2": " ",
        "subfields": [{"tag": "a", "content": value}],
    }


def construct_subfields_for_lcc(value: str, special_cutter: bool) -> list[dict]:
    if special_cutter:
        subfield_h = value[: value.index(" ")].strip()
        subfield_i = value[value.index(" ") :].strip()
    else:
        try:
            subfield_h = value[: value.index(".")].strip()
            subfield_i = value[value.index(".") :].strip()
        except ValueError:
            subfield_h = value[: value.index(" ")].strip()
            subfield_i = value[value.index(" ") :].strip()

    return [{"tag": "h", "content": subfield_h}, {"tag": "i", "content": subfield_i}]


def determine_safe_to_delete_item_callnumbers(items: list[dict]) -> set[str]:
    # callnumber belonging to other locations
    other_callnumbers = get_other_item_callnumbers(items)
    print(f"Other callnumbers: {other_callnumbers}")
    # callnumber unique to pam11 & pah11
    ref_callnumbers = get_ref_item_callnumbers(items)
    print(f"REF callnumbers: {ref_callnumbers}")

    callnumbers4del = set()
    for callnumber in ref_callnumbers:
        if callnumber not in other_callnumbers:
            callnumbers4del.add(callnumber)

    return callnumbers4del


def get_bib_callnumber(bib: dict) -> set[str]:
    callnumbers = set()
    for f in bib["varFields"]:
        if is_callnumber_field(f):
            callnumber = get_callnumber(f)
            norm_callnumber = normalize_callnumber(callnumber)
            callnumbers.add(norm_callnumber)
    return callnumbers


def get_other_item_callnumbers(items: list[dict]) -> set[str]:
    callnumbers = set()
    for i in items:
        if not is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_callnumber(f)
                    norm_callnumber = normalize_callnumber(callnumber)
                    # print(f"Norm callnumber: {norm_callnumber}")
                    callnumbers.add(norm_callnumber)
    return callnumbers


def get_ref_item_callnumbers(items: list[dict]) -> set[str]:
    callnumbers = set()
    for i in items:
        if is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_callnumber(f)
                    norm_callnumber = normalize_callnumber(callnumber)
                    callnumbers.add(norm_callnumber)
    return callnumbers


def get_callnumber(var_field: dict) -> str:
    """
    Takes all subfields and combines them into a string (including $m & $z)
    """
    elements = []
    try:
        for subfield in var_field["subfields"]:
            elements.append(subfield["content"].strip())
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


def is_lpa_ref_location(item: dict) -> bool:
    try:
        if item["location"]["code"] in ("pam11", "pah11"):
            return True
        else:
            return False
    except KeyError:
        return False


def normalize_callnumber(value: str) -> str:
    norm_value = re.sub(r'\.|,|\(|\)|"|-', "", value).strip()
    return norm_value


def dedup_orphan_callnumbers(callnumbers: set[str]) -> set[str]:
    norm_callnumbers = []
    deduped_callnumbers = set()
    for c in callnumbers:
        norm_c = normalize_callnumber(c)
        if norm_c in norm_callnumbers:
            continue
        else:
            norm_callnumbers.append(norm_c)
            deduped_callnumbers.add(c)
    return deduped_callnumbers


def update_bib_varFields(
    varFields: list[dict], callnumbers4del: set[str], other_loc_callnumbers: set[str]
) -> list[dict]:
    new_varFields = []
    orphan_callnumbers = set()
    for f in varFields:
        if is_callnumber_field(f):
            callnumber = get_callnumber(f)
            norm_callnumber = normalize_callnumber(callnumber)
            if norm_callnumber and norm_callnumber in callnumbers4del:
                orphan_callnumbers.add(callnumber)
            elif norm_callnumber not in other_loc_callnumbers:
                orphan_callnumbers.add(callnumber)
            else:
                new_varFields.append(f)
        else:
            new_varFields.append(f)
    print(f"Orphan callnumbers: {orphan_callnumbers}")
    deduped_orphan_callnumbers = dedup_orphan_callnumbers(orphan_callnumbers)
    for callnumber in deduped_orphan_callnumbers:
        new_947_field = construct_947_field(callnumber)
        new_varFields.append(new_947_field)

    return new_varFields
