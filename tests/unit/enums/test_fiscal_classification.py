import pytest
from sankhya_sdk.enums import FiscalClassification


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (FiscalClassification.FINAL_CUSTOMER, "C", "Consumidor Final"),
        (FiscalClassification.ICMS_FREE, "I", "Isento de ICMS"),
        (FiscalClassification.RURAL_PRODUCER, "P", "Produtor Rural"),
        (FiscalClassification.RETAILER, "R", "Revendedor"),
        (FiscalClassification.USE_TOP, "T", "Usar a da TOP"),
        (FiscalClassification.TAXPAYER_CUSTOMER, "X", "Consumidor Contribuinte"),
    ],
)
def test_fiscal_classification_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
