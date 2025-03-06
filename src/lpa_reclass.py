from lpa_reclass_utils import (
    change_varFields,
    connect2sierra,
    construct_subfields_for_lcc,
    construct_lcc_field,
    get_reclass_data,
    get_bib,
    get_item_nos_from_bib_response,
    get_items,
    new_classmarks,
)


def reclass(src_fh: str) -> None:
    data = get_reclass_data(src_fh)
    conn = connect2sierra()
    for sid, spec_cutter, new_value in data:
        bib = get_bib(sid, conn)
        bib_varFields = bib["varFields"]
        itemNos = get_item_nos_from_bib_response(bib["items"])

        # ?
        itemNos_str = get_items(",".join(itemNos), conn)
        items = get_items(sids=itemNos_str, conn=conn)

        classmark_lookup = create_classmark_lookup()
        classmarks4del = determine_safe_to_delete_classmarks()

        lcc_subfields = construct_subfields_for_lcc(new_value, spec_cutter)
        new_lcc_field = construct_lcc_field(lcc_subfields)
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
