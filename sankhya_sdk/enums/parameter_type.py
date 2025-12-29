from ._metadata import EnumMetadata, MetadataEnum


class ParameterType(MetadataEnum):
    """Representa o tipo de um parâmetro."""

    STRING = ("String", EnumMetadata(internal_value="S", human_readable="String"))
    INTEGER = ("Integer", EnumMetadata(internal_value="I", human_readable="Integer"))
    DATETIME = ("Datetime", EnumMetadata(internal_value="D", human_readable="Datetime"))
