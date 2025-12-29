from ._metadata import EnumMetadata, MetadataEnum


class InvoiceStatus(MetadataEnum):
    """Representa o status de uma fatura."""

    SERVICE = ("Service", EnumMetadata(internal_value="A", human_readable="Atendimento"))
    RELEASED = ("Released", EnumMetadata(internal_value="L", human_readable="Liberada"))
    PENDING = ("Pending", EnumMetadata(internal_value="P", human_readable="Pendente"))
