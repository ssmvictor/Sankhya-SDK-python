import pytest
from sankhya_sdk.enums import InvoiceStatus


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (InvoiceStatus.SERVICE, "A", "Atendimento"),
        (InvoiceStatus.RELEASED, "L", "Liberada"),
        (InvoiceStatus.PENDING, "P", "Pendente"),
    ],
)
def test_invoice_status_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
