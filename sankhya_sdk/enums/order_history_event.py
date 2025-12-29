from ._metadata import EnumMetadata, MetadataEnum


class OrderHistoryEvent(MetadataEnum):
    """Representa os eventos no histórico de pedidos."""

    NONE = ("None", EnumMetadata(internal_value="", human_readable="Nenhum"))
    CHANGE = ("Change", EnumMetadata(internal_value="A", human_readable="Alteração"))
    CONFIRMATION = ("Confirmation", EnumMetadata(internal_value="C", human_readable="Confirmação"))
    EXCLUSION = ("Exclusion", EnumMetadata(internal_value="E", human_readable="Exclusão"))
    INCLUSION = ("Inclusion", EnumMetadata(internal_value="I", human_readable="Inclusão"))
