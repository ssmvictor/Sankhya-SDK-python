from ._metadata import EnumMetadata, MetadataEnum


class FiscalPersonType(MetadataEnum):
    """Representa o tipo de uma pessoa fiscal."""

    INDIVIDUAL = ("Individual", EnumMetadata(internal_value="F", human_readable="Pessoa física"))
    CORPORATION = ("Corporation", EnumMetadata(internal_value="J", human_readable="Pessoa jurídica"))
