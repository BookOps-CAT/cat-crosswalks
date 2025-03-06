import csv
import json
import os
import re
from typing import Union, Optional, Generator
from urllib.parse import urlparse

from bookops_sierra import SierraSession, SierraToken


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


def construct_subfields_for_lcc(value: str, special_cutter: bool) -> list[dict]:
    if special_cutter:
        subfield_h = value[: value.index(" ")].strip()
        subfield_i = value[value.index(" ") :].strip()
    else:
        subfield_h = value[: value.index(".")].strip()
        subfield_i = value[value.index(".") :].strip()

    return [{"tag": "h", "content": subfield_h}, {"tag": "i", "content": subfield_i}]


def get_bib(sid: Union[str, int], conn: SierraSession) -> dict:
    res = conn.bib_get(sid, fields="varFields,items")
    print(f"Server response code: {res.status_code}")

    return res.json()


def update_bib(sid: Union[str, int], data: dict, conn: SierraSession) -> None:
    out = conn.bib_update(sid=sid, data=data, data_format="application/json")
    print(f"Update response code: {out.status_code}")


def is_callnumber_field(field: dict) -> bool:
    try:
        if field["marcTag"] == "852" and field["fieldTag"] in ("c", "q"):
            return True
        else:
            return False
    except KeyError:
        return False


def get_callnumber(field: dict) -> Optional[str]:
    try:
        callnumber = field["subfields"][0]["content"].strip()
    except (KeyError, IndexError):
        return None
    return callnumber


def is_for_deletion(callnumber: str, classmarks4del: list[str]) -> bool:
    print(callnumber, classmarks4del[0], callnumber in classmarks4del)
    if callnumber in classmarks4del:
        return True
    else:
        return False


def new_classmarks(varFields: list[dict], classmarks4del: list[str]) -> list:
    new_varFields = []
    for f in varFields:
        if is_callnumber_field(f):
            callnumber = get_callnumber(f)
            if is_for_deletion(callnumber, classmarks4del):
                pass
            else:
                new_varFields.append(f)
        else:
            new_varFields.append(f)
    return new_varFields


def has_special_cutter(value: str) -> bool:
    if "YES" in value.upper():
        return True
    else:
        return False


def get_reclass_data(fh: str) -> Generator[tuple[str, bool, str], None, None]:
    with open(fh, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            bibNo = row[1].strip()[1:-1]
            spec_cutter = has_special_cutter(row[2])
            lcc = row[3].strip()
            yield (bibNo, spec_cutter, lcc)


def construct_lcc(subfields: list[dict]) -> dict:
    return {
        "fieldTag": "q",
        "marcTag": "852",
        "ind1": "0",
        "ind2": "1",
        "subfields": subfields,
    }


def get_item_nos_from_bib_response(urls: list[str]) -> list[str]:
    return [u.rsplit("/", 1)[-1] for u in urls]


def normalize_callnumer(value: str) -> str:
    norm_value = re.sub(r'\.|,|\(|\)|"|-', "", value).strip()
    return norm_value


def get_subfield_contents(var_field: dict) -> str:
    elements = []
    try:
        for subfield in var_field["subfields"]:
            norm_content = normalize_callnum(subfield["content"])
            elements.append(norm_content)
    except KeyError:
        pass
    return " ".join(elements)


def get_items(sids: str, conn: SierraSession) -> list[dict]:
    res = conn.items_get(sids=sids, fields="location,varFields")
    items = res.json()["entries"]
    return items


def change_varFields(item: dict, lcc: str, lcc_cutter: str) -> list[dict]:
    new_varFields = []
    varFields = item["varFields"]
    for f in varFields:
        if f["fieldTag"] == "c" and f["marcTag"] == "852":
            callnum = construct_item_callnum_field(lcc, lcc_cutter)
            new_varFields.append(callnum)
        else:
            new_varFields.append(f)
    return new_varFields


def construct_item_callnum_field(lcc: str, lcc_cutter: str) -> dict:
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


def is_lpa_ref_location(item: dict) -> bool:
    try:
        if item["location"]["code"] in ("pam11", "pah11"):
            return True
        else:
            return False
    except KeyError:
        return False


def get_other_item_classmarks(items: dict) -> set[str]:
    classmarks = set()
    for i in items:
        if not is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_subfield_contents(f)
                    classmarks.add(callnumber)
    return classmarks


def get_ref_item_classmarks(items: dict) -> set[str]:
    classmarks = set()
    for i in items:
        if is_lpa_ref_location(i):
            for f in i["varFields"]:
                if is_callnumber_field(f):
                    callnumber = get_subfield_contents(f)
                    classmarks.add(callnumber)
    return classmarks


def determine_save_to_delete_classmarks(items: dict) -> set[str]:
    # classmarks belonging to other locations
    other_classmarks = get_other_item_classmarks(items)
    # classmarks unique to pam11 & pah11
    ref_classmarks = get_ref_item_classmarks(items)

    classmarks4del = set()
    for classmark in ref_classmarks:
        if classmark not in other_classmarks:
            classmarks4del.add(classmark)

    return classmarks4del


def get_bib_classmarks(bib: dict) -> set[str]:
    pass


def reclass(src_fh: str) -> None:
    data = get_reclass_data(src_fh)
    conn = connect2sierra()
    for sid, spec_cutter, new_value in data:
        bib = get_bib(sid, conn)
        bib_varFields = bib["varFields"]
        itemNos = get_item_nos_from_bib_response(bib["items"])
        itemNos_str = get_items(",".join(itemNos), conn)
        items = get_items(sids=itemNos_str, conn=conn)

        classmark_lookup = create_classmark_lookup()
        classmarks4del = determine_safe_to_delete_classmarks()

        lcc_subfields = construct_subfields_for_lcc(new_value, spec_cutter)
        new_lcc_field = construct_lcc(lcc_subfields)
        bib_new_varFields = new_classmarks(bib_varFields, classmarks4del)
        bib_new_varFields.append(new_lcc_field)

        # update item records
        for item in items:
            new_varFields = change_varFields(item, "AI3", ".M4")
            new_data = {"varFields": new_varFields}
            # res = conn.item_update(sid=item["id"], data=new_data)

        # update bib record
        data = {"varFields": bib_new_varFields}
        update_bib(sid, data, conn)


if __name__ == "__main__":
    # {'fieldTag': 'c', 'marcTag': '852', 'ind1': '8', 'ind2': ' ', 'subfields': [{'tag': 'h', 'content': 'JFD 92-6213'}]}
    data = get_reclass_data("src/files/LPALCReclass/LPAOpenShelfRef.csv")
    sid = "13213996"
    conn = connect2sierra()
    # bib = get_bib(sid, conn)
    # print(bib)
    items = get_items(sids="13213996", conn=conn)
    for item in items:
        new_varFields = change_varFields(item, "AI3", ".M4")
        new_data = {"varFields": new_varFields}
        # res = conn.item_update(sid=item["id"], data=new_data)
        # print(f"item {item["id"]}: {res.status_code}")
