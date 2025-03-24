import csv
from datetime import datetime
import logging
import json
import os
from typing import Generator, Union

from bookops_sierra.errors import BookopsSierraError
from bookops_sierra import SierraSession, SierraToken

from src.lpa_reclass_utils import (
    MultiCallNumError,
    change_item_varFields,
    cleanup_bib_varFields,
    construct_subfields_for_lcc,
    construct_lcc_field,
    determine_safe_to_delete_item_callnumbers,
    get_item_nos_from_bib_response,
    get_other_item_callnumbers,
    is_lpa_ref_location,
    item_is_updated,
    split_into_batches,
)
from src.utils import save2csv


logger = logging.getLogger(__name__)


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


def get_access_token():
    fh = os.path.join(os.environ["USERPROFILE"], ".cred/.sierra/sierra-prod-lpa.json")
    with open(fh, "r") as file:
        cred = json.load(file)
    token = SierraToken(
        client_id=cred["client_id"],
        client_secret=cred["client_secret"],
        host_url=cred["host_url"],
        agent="BOOKOPS/TESTS",
    )
    return token


def get_bib(sid: Union[str, int], conn: SierraSession) -> dict:
    res = conn.bib_get(sid, fields="varFields,items")
    return res.json()


def get_items(sids: str, conn: SierraSession) -> list[dict]:
    res = conn.items_get(sids=sids, fields="location,varFields")
    items = res.json()["entries"]
    return items


def update_bib(sid: Union[str, int], data: dict, conn: SierraSession) -> int:
    out = conn.bib_update(sid=sid, data=data, data_format="application/json")
    return out.status_code


def reclass(src_fh: str, row=2) -> None:

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

    # prep output files
    src_data = get_reclass_data(src_fh)
    log_fh = "src/files/LPALCReclass/LPAReclas-log.csv"
    save2csv(
        log_fh,
        ["timestamp", "bibNo", "lcc", "items_updated", "requests_made", "elapsed_time"],
    )
    errors_fh = "src/files/LPALCReclass/LPAReclass-errors.csv"

    # process
    token = get_access_token()
    with SierraSession(authorization=token, timeout=15, delay=1) as conn:
        logger.info("Established Sierra API session.")
        for sid, spec_cutter, lcc in src_data:
            req_no = 0
            # get Sierra bib data
            timestamp = datetime.now()
            try:
                req_no += 1
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
                req_no += 1
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
                if is_lpa_ref_location(item) and not item_is_updated(item):
                    try:
                        new_varFields = change_item_varFields(item, new_lcc_item_field)
                        lpa_ref_item_exists = True
                    except MultiCallNumError:
                        logger.error(f"MultiCallnumberError: b{sid}a. Skipping item.")
                        save2csv(errors_fh, [sid, item["id"]])
                        continue

                    new_item_data = {"varFields": new_varFields}
                    try:
                        req_no += 1
                        res = conn.item_update(sid=item["id"], data=new_item_data)
                        logger.debug(f"Updated item:{res.url}")
                        item_update_count += 1
                        items_updated.append(item["id"])
                    except BookopsSierraError:
                        logger.error(
                            f"BookopsSierraError: b{sid}a | {item["id"]}. Verify."
                        )
                        save2csv(errors_fh, [sid, item["id"]])
                        raise

            # update bib record
            if lpa_ref_item_exists:
                new_lcc_bib_field = construct_lcc_field(lcc_subfields, fieldTag="q")
                bib_new_varFields = cleanup_bib_varFields(
                    bib_varFields, callnumbers4del, other_loc_callnumbers
                )
                bib_new_varFields.append(new_lcc_bib_field)
                new_bib_data = {"varFields": bib_new_varFields}
                req_no += 1
                res = update_bib(sid, new_bib_data, conn)
                logger.debug(f"Updating b{sid}a ({row}) result: {res}")
                end = datetime.now()
                elapsed = end - timestamp
                logger.info(f"Saving b{sid}a actions to csv.")
                save2csv(
                    log_fh,
                    [
                        timestamp,
                        sid,
                        lcc,
                        item_update_count,
                        ",".join(items_updated),
                        req_no,
                        elapsed,
                    ],
                )
            row += 1


if __name__ == "__main__":
    # reclass("src/files/LPALCReclass/LPAOpenShelfRef-TEST.csv")
    reclass("src/files/LPALCReclass/LPAOpenShelfRef.csv")
