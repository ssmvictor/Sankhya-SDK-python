from ._metadata import EnumMetadata, MetadataEnum


class FiscalClassification(MetadataEnum):
    """Representa a classificação fiscal de uma entidade."""

    FINAL_CUSTOMER = ("FinalCustomer", EnumMetadata(internal_value="C", human_readable="Consumidor Final"))
    ICMS_FREE = ("IcmsFree", EnumMetadata(internal_value="I", human_readable="Isento de ICMS"))
    RURAL_PRODUCER = ("RuralProducer", EnumMetadata(internal_value="P", human_readable="Produtor Rural"))
    RETAILER = ("Retailer", EnumMetadata(internal_value="R", human_readable="Revendedor"))
    USE_TOP = ("UseTop", EnumMetadata(internal_value="T", human_readable="Usar a da TOP"))
    TAXPAYER_CUSTOMER = ("TaxpayerCustomer", EnumMetadata(internal_value="X", human_readable="Consumidor Contribuinte"))
