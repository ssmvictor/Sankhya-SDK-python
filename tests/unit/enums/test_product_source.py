import pytest
from sankhya_sdk.enums import ProductSource


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ProductSource.NATIONAL, "0", "0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8"),
        (ProductSource.FOREIGN_DIRECT_IMPORT, "1", "1 - Estrangeira, importação direta, exceto a indicada no código 6"),
        (ProductSource.FOREIGN_ACQUIRED_DOMESTIC_MARKET, "2", "2 - Estrangeira, adquirada no mercado interno, exceto a indicada no código 7"),
        (ProductSource.NATIONAL_FOREIGN_BETWEEN_40_AND_70, "3", "3 - Nacional, mercadoria ou bem com conteúdo de importação superior a 40% e inferior ou igual a 70%"),
        (ProductSource.NATIONAL_BASIC_PRODUCTION_PROCESSES, "4", "4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos"),
        (ProductSource.NATIONAL_FOREIGN_UNDER_40, "5", "5 - Nacional, mercadoria ou bem com conteúdo de importação inferior ou igual a 40%"),
        (ProductSource.FOREIGN_DIRECT_IMPORT_CAMEX, "6", "6 - Estrangeira, importação direta, sem similar nacional, constante em lista da CAMEX"),
        (ProductSource.FOREIGN_ACQUIRED_DOMESTIC_MARKET_CAMEX, "7", "7 - Estrangeira, adquirida no mercado interno, sem similar nacional, constante em lista da CAMEX"),
        (ProductSource.NATIONAL_FOREIGN_OVER_70, "8", "8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%"),
    ],
)
def test_product_source_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
