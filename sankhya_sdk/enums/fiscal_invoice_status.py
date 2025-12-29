from ._metadata import EnumMetadata, MetadataEnum


class FiscalInvoiceStatus(MetadataEnum):
    """Representa o status de uma nota fiscal."""

    SENT = ("Sent", EnumMetadata(internal_value="I", human_readable="Enviada"))
    DENIED = ("Denied", EnumMetadata(internal_value="D", human_readable="Denegada"))
    APPROVED = ("Approved", EnumMetadata(internal_value="A", human_readable="Aprovada"))
    WAITING_AUTHORIZATION = ("WaitingAuthorization", EnumMetadata(internal_value="E", human_readable="Aguardando autorização"))
    WAITING_CORRECTION = ("WaitingCorrection", EnumMetadata(internal_value="R", human_readable="Aguardando correção"))
    VALIDATION_ERROR = ("ValidationError", EnumMetadata(internal_value="V", human_readable="Com erro de validação"))
    PENDING_RETURN = ("PendingReturn", EnumMetadata(internal_value="P", human_readable="Pendente de retorno"))
    SENT_DPEC = ("SentDpec", EnumMetadata(internal_value="S", human_readable="Enviada DPEC"))
    NOT_NFE = ("NotNfe", EnumMetadata(internal_value="M", human_readable="Não é NF-e"))
    NOT_NFSE = ("NotNfse", EnumMetadata(internal_value="M", human_readable="Não é NFS-e"))
    NFE_THIRD = ("NfeThird", EnumMetadata(internal_value="T", human_readable="NF-e terceiro"))
