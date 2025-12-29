from ._metadata import EnumMetadata, MetadataEnum


class ReferenceLevel(MetadataEnum):
    """Representa o nível de referência."""

    NONE = ("None", EnumMetadata(human_readable="None"))
    FIRST = ("First", EnumMetadata(human_readable="First"))
    SECOND = ("Second", EnumMetadata(human_readable="Second"))
    THIRD = ("Third", EnumMetadata(human_readable="Third"))
    FOURTH = ("Fourth", EnumMetadata(human_readable="Fourth"))
    FIFTH = ("Fifth", EnumMetadata(human_readable="Fifth"))
    SIXTH = ("Sixth", EnumMetadata(human_readable="Sixth"))
