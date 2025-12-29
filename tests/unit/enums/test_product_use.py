import pytest
from sankhya_sdk.enums import ProductUse


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ProductUse.BY_PRODUCT, "1", "SubProduto"),
        (ProductUse.PROD_INTERMEDIATE, "2", "Prod.Intermediário"),
        (ProductUse.GIFT, "B", "Brinde"),
        (ProductUse.CONSUMPTION, "C", "Consumo"),
        (ProductUse.RESALE_BY_FORMULA, "D", "Revenda (por fórmula)"),
        (ProductUse.PACKAGE, "E", "Embalagem"),
        (ProductUse.GIFT_FISCAL_INVOICE, "F", "Brinde (NF)"),
        (ProductUse.PROPERTY, "I", "Imobilizado"),
        (ProductUse.FEEDSTOCK, "M", "Matéria prima"),
        (ProductUse.OTHER_INPUTS, "O", "Outros insumos"),
        (ProductUse.IN_PROCESS, "P", "Em processo"),
        (ProductUse.RESALE, "R", "Revenda"),
        (ProductUse.SERVICE, "S", "Serviço"),
        (ProductUse.THIRD, "T", "Terceiros"),
        (ProductUse.SALE_OWN_MANUFACTURING, "V", "Venda (fabricação própria)"),
    ],
)
def test_product_use_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
