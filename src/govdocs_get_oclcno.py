import csv
import json
import os

from bookops_worldcat import WorldcatAccessToken, MetadataSession

from utils import save2csv


def sierra_data_reader(fh: str):
    with open(fh, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            yield (row[0], row[1])


def get_token(fh: str) -> WorldcatAccessToken:
    with open(fh, "r") as f:
        d = json.load(f)
        token = WorldcatAccessToken(
            key=d["key"],
            secret=d["secret"],
            scopes=d["scope"],
            agent="tomaszkalata@bookops.org",
        )
        return token


def query_worldcat(token: WorldcatAccessToken, source_fh: str) -> None:
    with MetadataSession(authorization=token) as session:
        data = sierra_data_reader(source_fh)
        for oclcNo, bibNo in data:
            try:
                res = session.bib_get_current_oclc_number(oclcNo)
                print(f"query: {oclcNo} = {res.status_code}")
                res_json = res.json()
                new_oclcNo = res_json["controlNumbers"][0]["current"]
                save2csv(
                    "src/files/GovDocs/private/GovDocs-only-Sierra-250123-checked.csv",
                    [bibNo, new_oclcNo, oclcNo],
                )
            except:
                # log
                print(f"Failed on {oclcNo}, {bibNo}")
                raise


if __name__ == "__main__":
    cred_fh = os.path.join(os.environ["USERPROFILE"], ".oclc/nyp_overload.json")
    source_fh = "src/files/GovDocs/private/GovDocs-only-Sierra-250123.csv"
    token = get_token(cred_fh)
    query_worldcat(token, source_fh)
