from ._metadata import EnumMetadata, MetadataEnum


class InventoryType(MetadataEnum):
    """Representa o tipo de estoque."""

    OWN = ("Own", EnumMetadata(internal_value="P", human_readable="Próprio"))
    THIRD = ("Third", EnumMetadata(internal_value="T", human_readable="Terceiro"))
