import csv

# import pymarc
from pymarc import Field, Record  # import only these two pymarc classes
import sys


ARTICLES = ["The ", "A ", "An "]  # note trailing white space


def skip_char(title: str) -> str:
    """
    Calculates number of characters to skip for 245 2nd indicator

    Args:
        title:          title proper

    Returns:
        number of characters to skip as string
    """
    for a in ARTICLES:
        if title.startswith(a):
            return str(len(a))
    return "0"


def save2marc(record: Record, out: str = "out.mrc") -> None:
    """
    Appends a given record to MARC21 file.

    Args:
        record:         instance of pymarc `Record` class
        out:            path to MARC21 file, default: out.mrc
    """
    with open(out, "ab") as marcfile:
        marcfile.write(record.as_marc())


def create_record(row: list) -> Record:
    """
    Constructs pymarc `Record` based on list of elements

    Args:
        row:            list of strings

    Returns:
        `pymarc.Record` instance
    """
    # declare PyMARC record object
    item_load = Record(to_unicode=True, force_utf8=True)

    # define data fields in CSV file
    accession_number = row[0]
    creator = row[1]
    contributor = row[2]
    title = row[3]
    date = row[4]
    physical_desc_a = row[5]
    physical_desc_b = row[6]
    physical_desc_c = row[7]
    # artist_note = row[9]
    # inscription_note = row[10]
    gift_c = row[8]
    gift_a = row[9]
    gift_d = row[10]

    # write data to field variables
    field_099 = Field(
        tag="099", indicators=[" ", "9"], subfields=["a", accession_number]
    )

    # for 100 & 245 there should be two paths: one if there is a creator, second if there is none
    if creator.strip():
        field_100 = Field(
            tag="100", indicators=["1", " "], subfields=["a", creator]
        )
        field_245_1st_ind = "1"
    else:
        field_245_1st_ind = "0"

    # determine if title starts with any nonfiling characters
    # and create 245 field
    field_245_2nd_ind = skip_char(title)
    field_245 = Field(
        tag="245",
        indicators=[field_245_1st_ind, field_245_2nd_ind],
        subfields=["a", title],
    )

    field_264 = Field(
        tag="264",
        # indicators=['\\', '0'],  # use empty space for blank indicators
        indicators=[" ", "0"],  # use empty space for blank indicators
        subfields=["c", date],  # it would be great to use `date` to populate 008 MARC tag pos
    )

    # will need appropriate punctuation at the end of each subfield
    # can use f-strings to do that
    # we may want to consider empty values in subfields 'a' or 'b' -
    # their absence may alter the punctuation
    # field_300 = Field(
    #     tag='300',
    #     indicators=[' ', ' '],
    #     subfields=['a', physical_desc_a, 'b', physical_desc_b, 'c', physical_desc_c]
    # )
    field_300 = Field(
        tag="300",
        indicators=[" ", " "],
        subfields=[
            "a",
            f"{physical_desc_a} :",
            "b",
            f"{physical_desc_b} ;",
            "c",
            physical_desc_c,
        ],
    )

    field_541 = Field(
        tag="541",
        indicators=["0", " "],
        subfields=["c", gift_c, "a", gift_a, "d", gift_d],
    )
    field_700 = Field(
        tag="700", indicators=["1", " "], subfields=["a", contributor]
    )

    # add field variables to PyMARC record object
    item_load.leader = "00000nkm  2200000Ii 4500"
    item_load.add_ordered_field(field_099)
    item_load.add_ordered_field(field_100)
    item_load.add_ordered_field(field_245)
    item_load.add_ordered_field(field_264)
    item_load.add_ordered_field(field_300)
    item_load.add_ordered_field(field_541)
    item_load.add_ordered_field(field_700)

    return item_load


def csvmarcwriter(file):
    # Open your CSV File
    with open(file) as fh:
        itemread = csv.reader(fh)  # maybe a better name would be a simple 'reader'
        # this line below looks redundant, itemread is a generator that can be
        # looped over and each returned value is a list with individual record data,
        # using a csv.reader() generator has one big advantage -
        # it reads into memory one one line from the csv file at a time,
        # with large files to be processed that may be important - you may actually
        # run into memory problems when trying to load too many records into memory
        # at the same time - `list(itemread)`

        # itemlist = list(itemread)
        next(itemread)  # to skip the header row simply use `next()` over the iterator

        # iterate through each row of the CSV file (note, the header was skipped in line 20)
        for row in itemread:
            item_load = create_record(row)

            # append to output file
            save2marc(item_load, file_out)


if __name__ == "__main__":
    # if you use this construct you will be able to import `csvmarcwriter` into other modules
    # without
    file_in = sys.argv[1]
    file_out = sys.argv[2]
    csvmarcwriter(file_in, file_out)

    # To call the function, try:  marc_writer.py Sheet1.csv sheet1.mrc
