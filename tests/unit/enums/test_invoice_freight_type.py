import pytest
from sankhya_sdk.enums import InvoiceFreightType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (InvoiceFreightType.EXTRA_INVOICE, "N", "Extra nota"),
        (InvoiceFreightType.INCLUDED, "S", "Incluso"),
    ],
)
def test_invoice_freight_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
