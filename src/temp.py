from pymarc import Record, Field


record = Record()
record.add_field(
    Field(tag="541", indicators=["0", " "], subfields=["a", "foo", "b", "bar"])
)
record.add_field(
    Field(tag="541", indicators=["0", " "], subfields=["a", "baz", "b", "spam"])
)

for field in record.get_fields("541"):
    if field["a"]:
        field["a"] = field["a"] + ";"

    if field["b"]:
        field["b"] = field["b"] + ";"

print(record)
