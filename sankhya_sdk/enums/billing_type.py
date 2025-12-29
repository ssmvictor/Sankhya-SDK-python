from ._metadata import EnumMetadata, MetadataEnum


class BillingType(MetadataEnum):
    """Representa os diferentes tipos de faturamento."""

    NONE = ("None", EnumMetadata(internal_value="", human_readable="Nenhum"))
    NORMAL = ("Normal", EnumMetadata(internal_value="FaturamentoNormal", human_readable="Faturamento normal"))
    DIRECT = ("Direct", EnumMetadata(internal_value="FaturamentoDireto", human_readable="Faturamento direto"))
