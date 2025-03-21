from datetime import datetime
import logging

from bookops_sierra.errors import BookopsSierraError

from lpa_reclass_utils import (
    MultiCallNumError,
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
    split_into_batches,
    cleanup_bib_varFields,
    update_bib,
)
from utils import save2csv


logger = logging.getLogger(__name__)


def reclass(src_fh: str) -> None:

    # setup logging
    logging.basicConfig(
        filename="src/files/LPALCReclass/lpa-main-log.log",
        format="%(levelname)s|%(asctime)s|%(message)s",
        datefmt="%m-%d-%Y %I:%M:%S %p",
        encoding="utf-8",
        level=logging.DEBUG,
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)

    src_data = get_reclass_data(src_fh)
    log_fh = "src/files/LPALCReclass/LPAReclas-log.csv"
    save2csv(log_fh, ["timestamp", "bibNo", "lcc", "items updated", "elapsed_time"])
    errors_fh = "src/files/LPALCReclass/LPAReclass-errors.csv"
    conn = connect2sierra()
    logger.info("Established Sierra API session.")
    row = 0
    for sid, spec_cutter, lcc in src_data:
        # get Sierra bib data
        timestamp = datetime.now()
        try:
            bib = get_bib(sid, conn)
            logger.info(f"Retrieved b{sid}a")
        except BookopsSierraError:
            logger.error(f"BIB NOT FOUND: b{sid}a")
            save2csv(log_fh, [timestamp, sid, lcc, "ERROR-BIB NOT FOUND"])
            continue

        bib_varFields = bib["varFields"]

        # get Sierra item data
        itemNos = get_item_nos_from_bib_response(bib["items"])
        logger.debug(f"Bib b{sid}a has {len(itemNos)} items attached.")
        retrieved_items = []
        for batch in split_into_batches(itemNos, batch_size=5):
            itemNos_str = ",".join(batch)
            items = get_items(sids=itemNos_str, conn=conn)
            retrieved_items.extend(items)

        logger.info(f"Constructing new MARC fields for b{sid}a")
        callnumbers4del = determine_safe_to_delete_item_callnumbers(retrieved_items)
        other_loc_callnumbers = get_other_item_callnumbers(retrieved_items)
        logger.debug(f"Callnumbers4del: {callnumbers4del}")

        lcc_subfields = construct_subfields_for_lcc(lcc, spec_cutter)

        # update LPA REF item records
        new_lcc_item_field = construct_lcc_field(lcc_subfields, fieldTag="c")
        item_update_count = 0
        items_updated = []

        lpa_ref_item_exists = False
        for item in retrieved_items:
            if is_lpa_ref_location(item):
                try:
                    new_varFields = change_item_varFields(item, new_lcc_item_field)
                    lpa_ref_item_exists = True
                except MultiCallNumError:
                    logger.error(f"MultiCallnumberError: b{sid}a. Skipping item.")
                    save2csv(errors_fh, [sid, item["id"]])
                    continue

                new_item_data = {"varFields": new_varFields}
                res = conn.item_update(sid=item["id"], data=new_item_data)
                logger.debug(f"Update item request:{res.url}")
                item_update_count += 1
                items_updated.append(item["id"])

        # update bib record
        if lpa_ref_item_exists:
            new_lcc_bib_field = construct_lcc_field(lcc_subfields, fieldTag="q")
            bib_new_varFields = cleanup_bib_varFields(
                bib_varFields, callnumbers4del, other_loc_callnumbers
            )
            bib_new_varFields.append(new_lcc_bib_field)
            new_bib_data = {"varFields": bib_new_varFields}
            res = update_bib(sid, new_bib_data, conn)
            logger.debug(f"Updating b{sid}a ({row}) result: {res}")
            end = datetime.now()
            elapsed = end - timestamp
            logger.info(f"Saving b{sid}a actions to csv.")
            save2csv(
                "src/files/LPALCReclass/LPAReclas-log.csv",
                [
                    timestamp,
                    sid,
                    lcc,
                    item_update_count,
                    ",".join(items_updated),
                    elapsed,
                ],
            )
        row += 1


if __name__ == "__main__":
    reclass("src/files/LPALCReclass/LPAOpenShelfRef-TEST.csv")
    # reclass("src/files/LPALCReclass/LPAOpenShelfRef.csv")
