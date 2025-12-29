from ._metadata import EnumMetadata, MetadataEnum


class InvoiceFreightType(MetadataEnum):
    """Representa o tipo de frete de uma fatura."""

    EXTRA_INVOICE = ("ExtraInvoice", EnumMetadata(internal_value="N", human_readable="Extra nota"))
    INCLUDED = ("Included", EnumMetadata(internal_value="S", human_readable="Incluso"))
