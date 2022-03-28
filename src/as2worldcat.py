"""
Use to prepare marcxml exports from ArchivesSpace to be ingested into
Worldcat using OCLC's MetadataAPI.

XML records straight from the AT raise certain validation errors when created via API
and cannot be added to Worldcat.


Example of the validation error response from Metadata service:
<oclc:error>
    <oclc:code type="application">CAT-VALIDATION</oclc:code>
    <oclc:message>Record is invalid</oclc:message>
    <oclc:detail type="application/xml">
      <validationErrors xmlns="">
        <validationError type="fixed field">
          <field occurrence="1" name="000"/>
          <message>Invalid relationship - when Descriptive Cataloging Form (Leader/18) is equal to u, then Encoding Level (Leader/17) must not be equal to blank.</message>
        </validationError>
        <validationError type="fixed field">
          <field occurrence="1" name="008"/>
          <message>Invalid relationship - when Cataloging Source Code (008/39) is equal to d, then $a in 040 must be present.</message>
        </validationError>
        <validationError type="variable field">
          <field occurrence="1" name="040"/>
          <message>Invalid relationship - when 040 is present, then $c in 040 must be present.</message>
        </validationError>
      </validationErrors>
    </oclc:detail>
  </oclc:error>
  <id>http://worldcat.org/oclc/</id>
</entry>
"""
import os
import json

from pymarc import Field, MARCReader, Record
from pymarc.marcxml import record_to_xml, parse_xml_to_array

from bookops_worldcat import WorldcatAccessToken, MetadataSession


def marc2xml(marcfile: str):
    with open(marcfile, "rb") as file:
        reader = MARCReader(file)
        for record in reader:
            xmlstr = record_to_xml(record, namespace=True)
            yield xmlstr


def xml2marc(xmlfile: str) -> Record:
    """
    Serializes MARC XML to pymarc `Record` object
    for manipulation
    """
    with open(xmlfile, "r") as f:
        reader = parse_xml_to_array(f)
        for record in reader:
            yield record


def has_invalid_subfields(subfields):
    invalid = False
    for s in subfields:
        if "|" in s:
            invalid = True
            break
    return invalid


def manipulate_as_record(record: Record) -> None:
    """
    Manipulations are done inplace
    """
    record.leader = f"{record.leader[:17]}Ki{record.leader[19:]}"

    # fix indicators in 035
    record["035"].indicators = [" ", " "]

    record["040"].subfields = ["a", "NyBlHS", "b", "eng", "e", "dacs", "c", "BKL"]

    dates = record["245"]["f"].strip()
    record.add_ordered_field(
        Field(tag="264", indicators=[" ", "0"], subfields=["c", dates])
    )

    for field in record.get_fields("351"):
        new_subfields = ["a"]
        value = field["b"]
        value = value.replace("\n\n", " ")
        new_subfields.append(value)

        field.subfields = new_subfields

    for field in record.get_fields("500"):
        new_subfields = [s.replace("\n\n", " ") for s in field.subfields]
        field.subfields = new_subfields

    record.remove_fields("506")
    record.add_ordered_field(
        Field(
            tag="506",
            indicators=["1", " "],
            subfields=[
                "a",
                "Collection is open to the public, may only be used in the library and is not available through interlibrary loan. Library policy on photocopying will apply. Advance notice may be required.",
            ],
        )
    )

    for field in record.get_fields("544"):
        new_subfields = []
        value = field["n"]
        value = value.split("\n\n")
        n = len(value)
        i = 0
        for v in value:
            i += 1
            new_subfields.append("d")
            if i == n:
                new_subfields.append(v)
            else:
                new_subfields.append(f"{v};")

        # remove last semicolon
        field.subfields = new_subfields

    # fix LCSH subject subfield coding
    subjects = record.subjects()
    for term in subjects:
        if term.indicator2 == "0":
            if has_invalid_subfields(term.subfields):
                print(term.subfields)
                new_subfields = ["a"]
                malformed = term.subfields[1]
                sub_list = malformed.split("|")
                main = sub_list[0].strip()
                new_subfields.append(main)
                for s in sub_list[1:]:
                    sub = s[0]
                    new_sub = s[1:].strip()
                    new_subfields.append(sub)
                    new_subfields.append(new_sub)
                term.subfields = new_subfields

    return record


def save2marc(record, marcfile):
    with open(marcfile, "ab") as out:
        out.write(record.as_marc())


def get_token():
    creds_fh = os.path.join(os.environ["USERPROFILE"], ".oclc/bpl_overload.json")
    with open(creds_fh, "r") as f:
        cred = json.load(f)
        token = WorldcatAccessToken(
            key=cred["key"],
            secret=cred["secret"],
            scopes="WorldCatMetadataAPI",
            principal_id=cred["principal_id"],
            principal_idns=cred["principal_idns"],
            agent="tomaszkalata@bookops.org",
        )
    return token


if __name__ == "__main__":

    marcxml = "./files/CBH/2019_004-marc.xml"
    marcfile = f"{marcxml[:-4]}-PRC.mrc"
    reader = xml2marc(marcxml)
    for record in reader:
        bib = manipulate_as_record(record)
        print(bib)
        save2marc(bib, marcfile)

    token = get_token()
    with MetadataSession(authorization=token) as session:
        reader = marc2xml(marcfile)
        for record in reader:
            result = session.create_bib(inst="13437", instSymbol="BKL", xmldata=record)
            print(result.status_code)
            print(result.content)
