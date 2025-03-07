from datetime import datetime

from bookops_sierra.errors import BookopsSierraError

from lpa_reclass_utils import (
    change_item_varFields,
    connect2sierra,
    construct_subfields_for_lcc,
    construct_lcc_field,
    determine_safe_to_delete_item_callnumbers,
    get_other_item_callnumbers,
    get_reclass_data,
    get_bib,
    get_item_nos_from_bib_response,
    get_items,
    is_lpa_ref_location,
    update_bib_varFields,
    update_bib,
)
from utils import save2csv


def split_into_batches(lst: list[str], batch_size=5) -> list[list[str]]:
    return [lst[i : i + batch_size] for i in range(0, len(lst), batch_size)]


def reclass(src_fh: str) -> None:
    src_data = get_reclass_data(src_fh)
    log_fh = "src/files/LPALCReclass/LPAReclas-log.csv"
    save2csv(log_fh, ["timestamp", "bibNo", "lcc", "items updated"])
    conn = connect2sierra()
    row = 0
    for sid, spec_cutter, lcc in src_data:
        # get Sierra bib data
        try:
            bib = get_bib(sid, conn)
        except BookopsSierraError:
            print(f"BIB NOT FOUND: b{sid}a")
            continue

        bib_varFields = bib["varFields"]

        # get Sierra item data
        itemNos = get_item_nos_from_bib_response(bib["items"])
        retrieved_items = []
        for batch in split_into_batches(itemNos, batch_size=5):
            itemNos_str = ",".join(batch)
            items = get_items(sids=itemNos_str, conn=conn)
            retrieved_items.extend(items)

        print(f"Constructing new MARC fields for b{sid}a")
        callnumbers4del = determine_safe_to_delete_item_callnumbers(retrieved_items)
        other_loc_callnumbers = get_other_item_callnumbers(retrieved_items)
        print(f"Callnumbers4del: {callnumbers4del}")

        lcc_subfields = construct_subfields_for_lcc(lcc, spec_cutter)
        new_lcc_bib_field = construct_lcc_field(lcc_subfields, fieldTag="q")
        bib_new_varFields = update_bib_varFields(
            bib_varFields, callnumbers4del, other_loc_callnumbers
        )
        bib_new_varFields.append(new_lcc_bib_field)

        # update LPA REF item records
        new_lcc_item_field = construct_lcc_field(lcc_subfields, fieldTag="c")
        item_update_count = 0
        items_updated = []
        timestamp = datetime.now()
        for item in retrieved_items:
            if is_lpa_ref_location(item):
                new_varFields = change_item_varFields(item, new_lcc_item_field)
                new_item_data = {"varFields": new_varFields}
                res = conn.item_update(sid=item["id"], data=new_item_data)
                print(f"Update item request:{res.url}")
                item_update_count += 1
                items_updated.append(item["id"])

        # update bib record
        new_bib_data = {"varFields": bib_new_varFields}
        # print(new_bib_data)
        res = update_bib(sid, new_bib_data, conn)
        print(f"Updating b{sid}a ({row}) result: {res}")
        save2csv(
            "src/files/LPALCReclass/LPAReclas-log.csv",
            [timestamp, sid, lcc, item_update_count, ",".join(items_updated)],
        )
        row += 1


if __name__ == "__main__":
    reclass("src/files/LPALCReclass/LPAOpenShelfRef-TEST.csv")
    # reclass("src/files/LPALCReclass/LPAOpenShelfRef.csv")
