from ._metadata import EnumMetadata, MetadataEnum


class ProductSourceType(MetadataEnum):
    """Representa o tipo de origem de um produto."""

    NONE = ("None", EnumMetadata(internal_value="None", human_readable="None"))
    GROUP = ("Group", EnumMetadata(internal_value="G", human_readable="Group of product"))
    PRODUCT = ("Product", EnumMetadata(internal_value="P", human_readable="Product"))
