from ._metadata import EnumMetadata, MetadataEnum


class ProductSuggestionType(MetadataEnum):
    """Representa o tipo de sugestão de produto."""

    NONE = ("None", EnumMetadata(internal_value="None", human_readable="Nenhum"))
    ACCESSORY = ("Accessory", EnumMetadata(internal_value="A", human_readable="Acessório"))
    SUGGESTION = ("Suggestion", EnumMetadata(internal_value="S", human_readable="Sugestão"))
    BUY_TOGETHER = ("BuyTogether", EnumMetadata(internal_value="C", human_readable="Compre Junto"))
