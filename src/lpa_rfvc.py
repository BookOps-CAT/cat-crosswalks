import csv

from utils import save2csv


def count_unique(src: str) -> int:
    unique_bibnos = set()
    with open(src, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            unique_bibnos.add(row[0].strip())

    return len(unique_bibnos)


def read_sierra_export(src: str, out: str) -> None:
    with open(src, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="^")
        header = [
            "bibNo",
            "bibMatType",
            "t910",
            "callNo",
            "itemNos",
            "researchItem",
            "branchItem",
            "itemStatuses",
            "itemOpacMsgs",
            "itemTypes",
            "itemMsgs",
            "aeonNote",
        ]
        save2csv(out, header)
        next(reader)  # skip orig header
        for row in reader:
            # print(row)

            bibNo = row[0]
            bibMatType = row[1].strip()
            t910 = row[2].strip()
            if not t910:
                t910 = None
            callNo = row[3].strip()
            if not callNo:
                callNo = None

            # item records
            items = row[4:]

            researchItem = False
            branchItem = False
            itemNos = []
            itemStatuses = []
            itemOpacMsgs = []
            itemTypes = []
            itemMsgs = []
            aeonNote = False

            try:
                assert len(items) % 7 == 0
            except AssertionError:
                print(f"Invalid # of item elements in {row}")

            total_items = int(len(items) / 7)

            for n in range(total_items):
                itemNo = items[n]
                itemNos.append(itemNo)

                itemLoc = items[n + total_items]

                itemStatus = items[n + total_items * 2]

                itemOpacMsg = items[n + total_items * 3]
                itemType = items[n + total_items * 4]
                itemMsg = items[n + total_items * 5]
                item_notes = items[n + total_items * 6]

                # has research item attached
                if "ma" in itemLoc or "rc" in itemLoc:
                    researchItem = True
                elif "my" in itemLoc:
                    itemStatuses.append(itemStatus)
                    itemOpacMsgs.append(itemOpacMsg)
                    itemTypes.append(itemType)
                    itemMsgs.append(itemMsg)
                    for note in item_notes.split("@"):
                        if "aeon" in note.lower():
                            aeonNote = True
                else:
                    branchItem = True

            save2csv(
                out,
                [
                    bibNo,
                    bibMatType,
                    t910,
                    callNo,
                    ",".join(itemNos),
                    researchItem,
                    branchItem,
                    ",".join(itemStatuses),
                    ",".join(itemOpacMsgs),
                    ",".join(itemTypes),
                    ",".join(itemMsgs),
                    aeonNote,
                ],
            )


if __name__ == "__main__":
    # src = "./files/RFVC/LPA-RFVC-items.txt"
    # out = "./files/RFVC/LPA-RFVC-items-analysis.csv"
    # read_sierra_export(src, out)

    src = "./files/RFVC/non-circ-bibno-raw.txt"
    print(count_unique(src))
