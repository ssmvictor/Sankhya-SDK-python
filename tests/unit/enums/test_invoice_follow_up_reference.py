import pytest
from sankhya_sdk.enums import InvoiceFollowUpReference


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (InvoiceFollowUpReference.CONTACT, "C", "Contato"),
        (InvoiceFollowUpReference.COMPANY, "E", "Empresa"),
        (InvoiceFollowUpReference.FREIGHT, "F", "Frete"),
        (InvoiceFollowUpReference.VEHICLE, "I", "Veículo"),
        (InvoiceFollowUpReference.INVOICE, "N", "Nota"),
        (InvoiceFollowUpReference.PARTNER, "P", "Parceiro"),
        (InvoiceFollowUpReference.PRODUCT, "R", "Produto"),
        (InvoiceFollowUpReference.CARRIER, "T", "Transportadora"),
        (InvoiceFollowUpReference.SELLER, "V", "Vendedor"),
    ],
)
def test_invoice_follow_up_reference_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
