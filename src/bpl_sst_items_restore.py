"""
1. Check if there are any bibNos that have been deleted
2. Verify checkin & checkout loc mapping (not happening per Andrew H.)
3. Ask about status and other coding (Keron - "m" (missing), no internal notes)
"""

import csv
from collections import namedtuple

from pymarc import Record, Field


from utils import save2csv, save2marc


Item = namedtuple(
    "Item",
    [
        "loc",
        "checkin_loc",
        "checkout_loc",
        "bibNo",
        "itemNo",
        "barcode",
        "status",
        "internal_msg",
        "format",
        "item_type",
        "stat_category",
        "price",
        "callNo",
        "author",
        "title",
        "internal_note",
    ],
)


def parse_items(file: str):
    with open(file, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for item in map(Item._make, reader):
            yield item


def create_bib(item: Item) -> Record:
    bib = Record(force_utf8=True)
    title = create_title_field(item)
    bib.add_ordered_field(title)
    matchNo = create_matching_field(item)
    bib.add_ordered_field(matchNo)
    item = create_item_field(item)
    bib.add_ordered_field(item)
    return bib


def create_matching_field(item: Item) -> Field:
    return Field(
        tag="907", indicators=[" ", " "], subfields=["a", f".{item.bibNo.strip()}"]
    )


def create_title_field(item: Item) -> Field:
    return Field(
        tag="245",
        indicators=["0", "0"],
        subfields=["a", f"RESTORE: {item.title.strip()}"],
    )


def get_price(price: str) -> str:
    if not isinstance(price, str):
        raise TypeError

    price = float(price)
    return f"{price:.2f}"


def create_item_field(item: Item) -> Field:
    price = get_price(item.price.strip())
    return Field(
        tag="960",
        indicators=[" ", " "],
        subfields=[
            "i",
            item.barcode.strip(),
            "l",
            item.loc.strip(),
            "p",
            price,
            "q",
            item.stat_category.strip(),
            "s",
            "m",
            "r",
            item.format.strip(),
            "t",
            item.item_type.strip(),
        ],
    )


def get_bibNos(src: str, out: str):
    items = parse_items(src)
    for item in items:
        save2csv(out, [item.bibNo])


if __name__ == "__main__":
    src = "src/files/SST/SST-355-399.9999 zzzzz.csv"
    out = "src/files/SST/SST-355-399-230424.mrc"

    items = parse_items(src)
    for i in items:
        bib = create_bib(i)
        try:
            save2marc(out, bib)
        except UnicodeEncodeError:
            print(i.barcode)

    # out = "src/files/SST/bibNos.csv"
    # get_bibNos(src, out)
