"""
Script finds bibs based on wlo number in the MARC control field (001)
"""

import os

from pymarc import MARCReader

from utils import save2marc

wlos = [
    "wlo0000027016",
    "wlo0000027017",
    "wlo0000027021",
    "wlo0000027029",
    "wlo0000027032",
    "wlo0000027033",
    "wlo0000027035",
    "wlo0000027037",
    "wlo0000027046",
    "wlo0000027047",
    "wlo0000027050",
    "wlo0000027052",
    "wlo0000027058",
    "wlo0000027059",
    "wlo0000027069",
    "wlo0000027072",
    "wlo0000027078",
    "wlo0000027079",
    "wlo0000027089",
    "wlo0000027090",
    "wlo0000027092",
    "wlo0000027100",
    "wlo0000027104",
    "wlo0000027107",
    "wlo0000027109",
    "wlo0000027115",
    "wlo0000027116",
    "wlo0000027121",
    "wlo0000027122",
    "wlo0000027128",
    "wlo0000027133",
    "wlo0000027134",
    "wlo0000027137",
    "wlo0000027140",
    "wlo0000027148",
    "wlo0000027149",
    "wlo0000027150",
    "wlo0000027154",
    "wlo0000027157",
    "wlo0000027162",
    "wlo0000027166",
    "wlo0000027169",
    "wlo0000027172",
    "wlo0000027173",
    "wlo0000027176",
    "wlo0000027180",
    "wlo0000027181",
    "wlo0000027185",
    "wlo0000027187",
    "wlo0000027192",
    "wlo0000027204",
    "wlo0000027210",
    "wlo0000027211",
    "wlo0000027212",
    "wlo0000027213",
    "wlo0000027215",
    "wlo0000027219",
    "wlo0000027220",
    "wlo0000027238",
    "wlo0000027242",
    "wlo0000027243",
    "wlo0000027245",
    "wlo0000027248",
    "wlo0000027249",
]


src = os.path.join(
    os.environ["USERPROFILE"], "Desktop/Temp/BKL-Casalini Libri-210823.mrc"
)
dst = os.path.join(
    os.environ["USERPROFILE"], "Desktop/Temp/BKL-missing-clibr-20180425-1.mrc"
)

with open(src, "rb") as marcfile:
    reader = MARCReader(marcfile)
    n = 0
    for bib in reader:
        n += 1
        controlNo = bib["001"].data
        if controlNo in wlos:
            save2marc(dst, bib)

    print(f"Found {n} bibs in file {src}")
