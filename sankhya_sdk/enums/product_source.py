from ._metadata import EnumMetadata, MetadataEnum


class ProductSource(MetadataEnum):
    """Representa a origem de um produto."""

    NATIONAL = ("National", EnumMetadata(internal_value="0", human_readable="0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8"))
    FOREIGN_DIRECT_IMPORT = ("ForeignDirectImport", EnumMetadata(internal_value="1", human_readable="1 - Estrangeira, importação direta, exceto a indicada no código 6"))
    FOREIGN_ACQUIRED_DOMESTIC_MARKET = ("ForeignAcquiredDomesticMarket", EnumMetadata(internal_value="2", human_readable="2 - Estrangeira, adquirada no mercado interno, exceto a indicada no código 7"))
    NATIONAL_FOREIGN_BETWEEN_40_AND_70 = ("NationalForeignBetween40And70", EnumMetadata(internal_value="3", human_readable="3 - Nacional, mercadoria ou bem com conteúdo de importação superior a 40% e inferior ou igual a 70%"))
    NATIONAL_BASIC_PRODUCTION_PROCESSES = ("NationalBasicProductionProcesses", EnumMetadata(internal_value="4", human_readable="4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos"))
    NATIONAL_FOREIGN_UNDER_40 = ("NationalForeignUnder40", EnumMetadata(internal_value="5", human_readable="5 - Nacional, mercadoria ou bem com conteúdo de importação inferior ou igual a 40%"))
    FOREIGN_DIRECT_IMPORT_CAMEX = ("ForeignDirectImportCamex", EnumMetadata(internal_value="6", human_readable="6 - Estrangeira, importação direta, sem similar nacional, constante em lista da CAMEX"))
    FOREIGN_ACQUIRED_DOMESTIC_MARKET_CAMEX = ("ForeignAcquiredDomesticMarketCamex", EnumMetadata(internal_value="7", human_readable="7 - Estrangeira, adquirida no mercado interno, sem similar nacional, constante em lista da CAMEX"))
    NATIONAL_FOREIGN_OVER_70 = ("NationalForeignOver70", EnumMetadata(internal_value="8", human_readable="8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%"))
