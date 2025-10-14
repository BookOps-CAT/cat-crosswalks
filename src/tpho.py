import csv
import os
import json
from typing import Generator

from bookops_sierra import SierraSession, SierraToken


def get_item_callnos(src: str) -> Generator[tuple[str, str], None, None]:
    with open(src, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            itemNo = row[0].strip()[1:-1]
            new_callno = row[2].strip()
            yield (itemNo, new_callno)


def connect2sierra():
    fh = os.path.join(os.environ["USERPROFILE"], ".cred/.sierra/sierra-dev.json")
    with open(fh, "r") as file:
        cred = json.load(file)
    print("Requesting access token")
    token = SierraToken(
        cred["client_id"],
        cred["client_secret"],
        cred["host_url"],
        cred["agent"],
        timeout=5,
    )
    print(f"token: {token.text}")
    with SierraSession(authorization=token, timeout=10) as session:
        return session


def update_item_callno(itemno: str, new_callno: str, conn: SierraSession) -> None:
    res = conn.item_get(sid=itemno, fields="varFields")
    print(f"Item request: {res.url}")
    print(res.json())
