import pytest
from sankhya_sdk.enums import FiscalInvoiceStatus


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (FiscalInvoiceStatus.SENT, "I", "Enviada"),
        (FiscalInvoiceStatus.DENIED, "D", "Denegada"),
        (FiscalInvoiceStatus.APPROVED, "A", "Aprovada"),
        (FiscalInvoiceStatus.WAITING_AUTHORIZATION, "E", "Aguardando autorização"),
        (FiscalInvoiceStatus.WAITING_CORRECTION, "R", "Aguardando correção"),
        (FiscalInvoiceStatus.VALIDATION_ERROR, "V", "Com erro de validação"),
        (FiscalInvoiceStatus.PENDING_RETURN, "P", "Pendente de retorno"),
        (FiscalInvoiceStatus.SENT_DPEC, "S", "Enviada DPEC"),
        (FiscalInvoiceStatus.NOT_NFE, "M", "Não é NF-e"),
        (FiscalInvoiceStatus.NOT_NFSE, "M", "Não é NFS-e"),
        (FiscalInvoiceStatus.NFE_THIRD, "T", "NF-e terceiro"),
    ],
)
def test_fiscal_invoice_status_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
