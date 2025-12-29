from ._metadata import EnumMetadata, MetadataEnum


class SystemParameterType(MetadataEnum):
    """Representa o tipo de um parâmetro de sistema."""

    NONE = ("None", EnumMetadata(internal_value="", human_readable="Nenhum"))
    TEXT = ("Text", EnumMetadata(internal_value="T", human_readable="Texto"))
    DATE = ("Date", EnumMetadata(internal_value="D", human_readable="Data"))
    DECIMAL = ("Decimal", EnumMetadata(internal_value="F", human_readable="Número Decimal"))
    LOGICAL = ("Logical", EnumMetadata(internal_value="L", human_readable="Lógico"))
    LIST = ("List", EnumMetadata(internal_value="C", human_readable="List"))
    INTEGER = ("Integer", EnumMetadata(internal_value="I", human_readable="Número Inteiro"))
