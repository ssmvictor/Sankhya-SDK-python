from sankhya_sdk.enums._metadata import EnumMetadata, MetadataEnum


def test_enum_metadata_instantiation():
    metadata = EnumMetadata(internal_value="val", human_readable="Readable")
    assert metadata.internal_value == "val"
    assert metadata.human_readable == "Readable"
    assert metadata.service_module is None


def test_metadata_enum_properties():
    class MockEnum(MetadataEnum):
        MEMBER = ("Member", EnumMetadata(internal_value="m", human_readable="Human"))
        SIMPLE = ("Simple", None)

    assert MockEnum.MEMBER.value == "Member"
    assert MockEnum.MEMBER.internal_value == "m"
    assert MockEnum.MEMBER.human_readable == "Human"
    assert isinstance(MockEnum.MEMBER.metadata, EnumMetadata)

    assert MockEnum.SIMPLE.value == "Simple"
    assert MockEnum.SIMPLE.internal_value == "Simple"
    assert MockEnum.SIMPLE.human_readable == "SIMPLE"


def test_metadata_enum_str():
    class MockEnum(MetadataEnum):
        MEMBER = ("Member", EnumMetadata(internal_value="m"))

    assert str(MockEnum.MEMBER) == "m"
