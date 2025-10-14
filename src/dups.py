from pymarc import MARCReader
import csv
from utils import save2csv


control_nos = []
dup_control_nos = []


def find_dups():
    with open("./files/flourish-all-prc.mrc", "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            control_no = bib["001"].data.strip()
            if control_no in control_nos:
                dup_control_nos.append(control_no)
            else:
                control_nos.append(control_no)

        print(f"found {len(dup_control_nos)} in the set.")
        print(f"{len(set(dup_control_nos))}")
        print(dup_control_nos)


def find_dup_control_nos():
    with open("./files/flourish-Sierra-all-220201.txt", "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        unique = set()

        for row in reader:
            if row[0] in unique:
                save2csv("./files/flourish4deletion.csv", [row[1]])
            else:
                unique.add(row[0])


find_dup_control_nos()
