from ._metadata import EnumMetadata, MetadataEnum


class InvoiceFollowUpReference(MetadataEnum):
    """Representa a referência para o acompanhamento de faturas."""

    CONTACT = ("Contact", EnumMetadata(internal_value="C", human_readable="Contato"))
    COMPANY = ("Company", EnumMetadata(internal_value="E", human_readable="Empresa"))
    FREIGHT = ("Freight", EnumMetadata(internal_value="F", human_readable="Frete"))
    VEHICLE = ("Vehicle", EnumMetadata(internal_value="I", human_readable="Veículo"))
    INVOICE = ("Invoice", EnumMetadata(internal_value="N", human_readable="Nota"))
    PARTNER = ("Partner", EnumMetadata(internal_value="P", human_readable="Parceiro"))
    PRODUCT = ("Product", EnumMetadata(internal_value="R", human_readable="Produto"))
    CARRIER = ("Carrier", EnumMetadata(internal_value="T", human_readable="Transportadora"))
    SELLER = ("Seller", EnumMetadata(internal_value="V", human_readable="Vendedor"))
