import csv

from pymarc import MARCReader

from utils import save2marc


def get_oclcNos(csvfile: str) -> set[int]:

    oclcNos = set()
    with open(csvfile, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            oclcNos.add(int(row[0].strip()))
    return oclcNos


def select_bibs(oclcNos: set[int], src: str, out: str) -> None:
    count = 0
    with open(src, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            if int(bib["001"].data) in oclcNos:
                save2marc(out, bib)
                count += 1
    print(f"Saved {count} bibs to {out}")


if __name__ == "__main__":
    csvfile = "src/files/GovDocs/private/GovDocs-eres-matched-oclcNos.csv"
    srcmarc = "src/files/GovDocs/private/OCLC-dump-20250124.mrc"
    outmarc = "src/files/GovDocs/private/GovDocs-eres-matched.mrc"
    oclcNos = get_oclcNos(csvfile)
    select_bibs(oclcNos, srcmarc, outmarc)
