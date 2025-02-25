from utils import save2csv


def get_marcfile_name(value: str):
    pos = value.find(".errlog")
    name = value[14:pos]
    return name


def parse_report(fh: str) -> tuple[str, list[tuple[str, str]]]:
    titles = []
    lines = []
    marcfile = ""
    with open(fh, "r") as report:
        for line in report:
            lines.append(line)
            if "File Name:" in line:
                marcfile = get_marcfile_name(line)

    pos = 0
    for line in lines:
        if "inserted /" in line:
            part1 = line[69:].strip()
            block = line[8:14]
            if "inserted /" not in lines[pos + 1]:
                part2 = lines[pos + 1].strip()
            else:
                part2 = ""
            title = f"{part1} {part2}".strip()
            if title:
                titles.append((block, title))
        pos += 1

    return (marcfile, titles)


def save_data(marcfile: str, data: list[tuple[str, str]], out: str) -> None:
    save2csv(out, [marcfile, ""])
    save2csv(out, ["file block", "title"])
    for elem in data:
        save2csv(out, elem)


if __name__ == "__main__":
    fh = "src/files/GovDocs/private/FTS MAIL.eml"
    marcfile, titles = parse_report(fh)
    print(f"Found {len(titles)} errors in the report.")
    out = f"src/files/GovDocs/private/{marcfile}.csv"
    save_data(marcfile, titles, out)
