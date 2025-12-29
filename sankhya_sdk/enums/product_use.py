from ._metadata import EnumMetadata, MetadataEnum


class ProductUse(MetadataEnum):
    """Representa o uso de um produto."""

    BY_PRODUCT = ("ByProduct", EnumMetadata(internal_value="1", human_readable="SubProduto"))
    PROD_INTERMEDIATE = ("ProdIntermediate", EnumMetadata(internal_value="2", human_readable="Prod.Intermediário"))
    GIFT = ("Gift", EnumMetadata(internal_value="B", human_readable="Brinde"))
    CONSUMPTION = ("Consumption", EnumMetadata(internal_value="C", human_readable="Consumo"))
    RESALE_BY_FORMULA = ("ResaleByFormula", EnumMetadata(internal_value="D", human_readable="Revenda (por fórmula)"))
    PACKAGE = ("Package", EnumMetadata(internal_value="E", human_readable="Embalagem"))
    GIFT_FISCAL_INVOICE = ("GiftFiscalInvoice", EnumMetadata(internal_value="F", human_readable="Brinde (NF)"))
    PROPERTY = ("Property", EnumMetadata(internal_value="I", human_readable="Imobilizado"))
    FEEDSTOCK = ("Feedstock", EnumMetadata(internal_value="M", human_readable="Matéria prima"))
    OTHER_INPUTS = ("OtherInputs", EnumMetadata(internal_value="O", human_readable="Outros insumos"))
    IN_PROCESS = ("InProcess", EnumMetadata(internal_value="P", human_readable="Em processo"))
    RESALE = ("Resale", EnumMetadata(internal_value="R", human_readable="Revenda"))
    SERVICE = ("Service", EnumMetadata(internal_value="S", human_readable="Serviço"))
    THIRD = ("Third", EnumMetadata(internal_value="T", human_readable="Terceiros"))
    SALE_OWN_MANUFACTURING = ("SaleOwnManufacturing", EnumMetadata(internal_value="V", human_readable="Venda (fabricação própria)"))
