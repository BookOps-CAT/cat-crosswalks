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

from pymarc import MARCReader
from pymarc.marcxml import record_to_xml


def fix_and_save_to_marc(xml_file: str):
    reader = parse_xml_to_array(xml_file)
    marcfile = f"{xml_file[:-4]}-PRC.mrc"
    for record in reader:
        # manipulate leader of each record
        record.leader = f"{record.leader[:17]}ii{record.leader[19:]}"
        record["035"].indicators = [" ", " "]
        record["040"].subfields = ["a", "BKL", "b", "eng", "e", "rda", "c", "BKL"]

        with open(marcfile, "ab") as out:
            out.write(record.as_marc())


def marc2xml(marcfile: str):
    with open(marcfile, "rb") as file:
        reader = MARCReader(file)
        for record in reader:
            xmlstr = record_to_xml(record, namespace=True)
            yield xmlstr


if __name__ == "__main__":
    fh = "./files/BCMS.0082_20210930_203437_UTC__marc21.xml"
    fix_and_save_to_marc(fh)
