import pytest
from sankhya_sdk.enums import BillingType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (BillingType.NONE, "", "Nenhum"),
        (BillingType.NORMAL, "FaturamentoNormal", "Faturamento normal"),
        (BillingType.DIRECT, "FaturamentoDireto", "Faturamento direto"),
    ],
)
def test_billing_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
